from playwright.sync_api import sync_playwright

# ================== HELPERS GÉNÉRIQUES ==================

def select_dropdown(page, label, value):
    # input Vuetify avec placeholder (évite les inputs "masqués")
    input_box = page.locator(f"label:has-text('{label}') + div input[placeholder]").first
    input_box.click()
    page.wait_for_selector("div.v-overlay-container .v-list-item-title", state="visible")
    page.locator("div.v-overlay-container .v-list-item-title", has_text=value).first.click()
    print(f"✅ {label} sélectionné : {value}")

def fill_input(page, label, value):
    page.wait_for_selector(f"label:has-text('{label}')")
    input_box = page.locator(f"label:has-text('{label}')").locator("xpath=..").locator("input")
    input_box.fill(str(value))
    print(f"✅ {label} rempli : {value}")

def safe_fill_input(el, value: str):
    try: el.scroll_into_view_if_needed()
    except Exception: pass
    try:
        el.fill(value); el.page.wait_for_timeout(100); return
    except Exception: pass
    try:
        el.click(); el.page.keyboard.press("Control+A"); el.type(value, delay=15)
    except Exception: pass
    el.page.wait_for_timeout(100)

def get_active_panel(page):
    pnl = page.locator('[role="tabpanel"]:visible, .v-window-item--active').first
    return pnl if pnl.count() else None

def _scope(panel_or_none, page, selector: str):
    if panel_or_none:
        nodes = panel_or_none.locator(selector)
        if nodes.count(): return nodes
    return page.locator(selector)

def save_current_section(page, panel=None, label="section"):
    # Ferme tout menu/overlay éventuel
    for _ in range(2):
        try: page.keyboard.press("Escape")
        except Exception: pass
        page.wait_for_timeout(120)
    for attempt in range(2):
        try:
            btns = _scope(panel, page, "button:has-text('Enregistrer')")
            btn = btns.filter(has_not=page.locator('[aria-hidden="true"]')).last
            if not btn.count(): btn = page.locator("button:has-text('Enregistrer')").last
            btn.scroll_into_view_if_needed(); btn.click(force=True)
            page.wait_for_load_state("networkidle"); page.wait_for_timeout(350)
            print(f"💾 Enregistré ({label}) [tentative {attempt+1}]"); return True
        except Exception:
            page.wait_for_timeout(300)
    print(f"⚠️ Impossible d'enregistrer ({label}), on poursuit."); return False

# ================== CATÉGORIES DE DONNÉES ==================

def ajouter_categorie_donnees(page, donnee):
    """
    donnee = {
      "categorie_label": "... (libellé EXACT DP-Manager)",
      "type": "Données perssonelles" | "Données professionnelles" | "Données financières" | "Données sensibles",
      "origine": "Personne concernées",
      "utilise": "Oui",
      "source": "Formulaires en ligne" | "Système d'information" | "Dossiers papiers" | "Justificatifs fournis",
      "duree_type": "Limitée",
      "duree": 24/36/120,
      "declencheur": "Fin de la session" | "Clôture de l’exercice comptable" | ...
    }
    """
    print(f"➡️ Ajout (Catégorie de données) : {donnee['categorie_label']}")
    page.get_by_role("button", name="Ajouter").first.click()
    page.wait_for_timeout(500)

    # Catégorie des données (sélection par libellé EXACT)
    page.locator("label:has-text('Catégorie des données') + div input").click()
    page.wait_for_selector("div.v-overlay-container .v-list-item-title", state="visible")
    page.locator("div.v-overlay-container .v-list-item-title", has_text=donnee["categorie_label"]).first.click()
    print(f"✅ Catégorie sélectionnée : {donnee['categorie_label']}")

    # Type / Origine / Utilisé / Source
    select_dropdown(page, "Type des données", donnee["type"])
    select_dropdown(page, "Origine de la donnée", donnee["origine"])
    select_dropdown(page, "Utilisé(s) pour la finalité du traitement", donnee["utilise"])
    select_dropdown(page, "Source de données", donnee["source"])

    # Durée / Déclencheur
    if donnee["duree_type"] != "Limitée":
        select_dropdown(page, "Durée de conservation", donnee["duree_type"])
    else:
        print("ℹ️ Durée de conservation par défaut = Limitée")
    fill_input(page, "Préciser la durée (mois)", donnee["duree"])
    fill_input(page, "Élément déclencheur", donnee["declencheur"])

    save_current_section(page, label=f"Catégorie: {donnee['categorie_label']}")
    print("✅ Catégorie de données ajoutée")

# ================== FINALITÉ ==================

def remplir_finalite(page, finalite_fr, finalite_ar):
    print("➡️ Remplissage de la section Finalité")
    menu_item = page.get_by_text("Finalité", exact=True)
    menu_item.scroll_into_view_if_needed(); menu_item.click(force=True)
    page.wait_for_timeout(600)

    textarea_fr = page.locator("label:has-text('Finalité (but) du traitement')").locator("xpath=..").locator("textarea")
    textarea_fr.fill(finalite_fr); print("✅ Finalité FR remplie")

    textarea_ar = page.locator("label:has-text('الغاية (الهدف) من المعالجة')").locator("xpath=..").locator("textarea")
    textarea_ar.fill(finalite_ar); print("✅ Finalité AR remplie")

    save_current_section(page, label="Finalité")
    print("✅ Section Finalité enregistrée")

# ================== SOUS-TRAITEMENTS ==================

def ajouter_sous_traitement(page, st):
    print(f"➡️ Ajout (Sous-traitement) : {st['denomination_fr']} / {st['denomination_ar']}")
    page.get_by_role("button", name="Ajouter").first.click()
    page.wait_for_timeout(500)

    modal = page.locator("div.v-overlay-container").last
    denom_fr = modal.locator("input").nth(0); denom_fr.wait_for(state="visible", timeout=5000); denom_fr.fill(st["denomination_fr"])
    denom_ar = modal.locator("input").nth(1); denom_ar.wait_for(state="visible", timeout=5000); denom_ar.fill(st["denomination_ar"])
    print("✅ Dénominations FR/AR remplies")

    type_input = modal.locator("label:has-text('Type de traitement') + div input").first
    type_input.click(); page.wait_for_selector("div.v-overlay-container .v-list-item-title", state="visible")
    for t in st["types"]:
        page.locator("div.v-overlay-container .v-list-item-title", has_text=t).first.click()
        print(f"✅ Type sélectionné : {t}")
    page.keyboard.press("Escape")

    select_dropdown(page, "Base légale", st["base_legale"])
    if st.get("sous_traitant"): select_dropdown(page, "Sous traitant", st["sous_traitant"])
    if st.get("logiciel"): select_dropdown(page, "Logiciel utilisé", st["logiciel"])

    modal.locator("textarea").last.fill(st["note"])
    modal.locator("button:has-text('Enregistrer')").last.click()
    page.wait_for_timeout(700)
    print("✅ Sous-traitement ajouté")

# ================== CONSERVATION DES DONNÉES ==================

def ajouter_conservation_donnees(page, conservation):
    print("➡️ Ajout (Conservation des données)")
    onglet = page.get_by_text("Conservation des données", exact=True)
    onglet.scroll_into_view_if_needed(); onglet.click(force=True)
    page.wait_for_load_state("networkidle"); page.wait_for_timeout(300)

    def fill_by_label(label_text: str, value: str):
        lab = page.locator(f"label:has-text('{label_text}')").first
        lab.wait_for(state="visible", timeout=8000)
        inp = lab.locator("xpath=..").locator("input, textarea").first
        inp.wait_for(state="visible", timeout=8000)
        inp.fill(value)

    def ensure_checked(name_substring: str):
        cb = page.get_by_role("checkbox", name=name_substring, exact=False).first
        cb.wait_for(state="visible", timeout=8000)
        try:
            if not cb.is_checked(): cb.check(force=True)
        except Exception: cb.click(force=True)

    if "Manuel" in conservation["modes"]: ensure_checked("Manuel"); print("☑️ Manuel coché")
    if "Informatique" in conservation["modes"]: ensure_checked("Informatique"); print("☑️ Informatique coché")

    if "informatique" in conservation:
        fill_by_label("Nom de la base de données", conservation["informatique"]["nom"])
        fill_by_label("Lieu de stockage de la base de données", conservation["informatique"]["lieu"])
        print("✅ Conservation informatique remplie")

    if "manuel" in conservation:
        fill_by_label("Nom du fichier manuel", conservation["manuel"]["nom"])
        fill_by_label("Lieu de stockage du fichier", conservation["manuel"]["lieu"])
        print("✅ Conservation manuelle remplie")

    save_current_section(page, label="Conservation des données")

# ================== DESTINATAIRES ==================

def modal_select_dropdown(modal, label, value):
    input_box = modal.locator(f"label:has-text('{label}') + div input[placeholder]").first
    input_box.click()
    modal.page.wait_for_selector("div.v-overlay-container .v-list-item-title", state="visible")
    modal.page.locator("div.v-overlay-container .v-list-item-title", has_text=value).first.click()
    print(f"✅ {label} sélectionné : {value}")

def modal_fill(modal, label, value):
    field = modal.locator(f"label:has-text('{label}')").locator("xpath=..").locator("textarea, input").first
    field.fill(str(value))

def ajouter_un_destinataire(page, d):
    page.get_by_role("button", name="Ajouter").first.click()
    page.wait_for_timeout(300)
    modal = page.locator("div.v-overlay-container").last

    dest_input = modal.locator("label:has-text('Destinataire') + div input").first
    dest_input.click()
    if d.get("destinataire"):
        dest_input.fill(d["destinataire"]); modal.page.wait_for_timeout(200)
    modal.page.wait_for_selector("div.v-overlay-container .v-list-item-title", state="visible")
    modal.page.locator("div.v-overlay-container .v-list-item-title", has_text=d["destinataire"]).first.click()
    print(f"✅ Destinataire sélectionné : {d['destinataire']}")

    if d.get("moyen"): modal_select_dropdown(modal, "Moyen de communication", d["moyen"])
    if d.get("cadre_legal") is not None: modal_select_dropdown(modal, "Cadre legal", "Oui" if d["cadre_legal"] else "Non")
    if d.get("objectifs"): modal_fill(modal, "Objectifs", d["objectifs"])
    if d.get("observation"): modal_fill(modal, "Observation", d["observation"])

    modal.locator("button:has-text('Enregistrer')").last.click()
    page.wait_for_timeout(600)
    print("💾 Destinataire ajouté")

def ajouter_destinataires(page, items):
    print("➡️ Section Destinataires : ajout")
    onglet = page.get_by_text("Les destinataires des données", exact=True)
    onglet.scroll_into_view_if_needed(); onglet.click(force=True)
    page.wait_for_timeout(500)
    for d in items: ajouter_un_destinataire(page, d)
    save_current_section(page, label="Destinataires")
    print("✅ Destinataires enregistrés")

# ================== CONSENTEMENT ==================

def ajouter_consentement(page, consent):
    print("➡️ Ajout (Consentement)")
    onglet = page.get_by_text("Consentement", exact=True)
    onglet.scroll_into_view_if_needed(); onglet.click(force=True)
    page.wait_for_timeout(500)

    select_dropdown(page, "Consentement des personnes concernées : Existe ?", "Oui" if consent.get("existe", True) else "Non")

    ta_fr = page.locator("label:has-text('Indiquer la méthode de consentement')").locator("xpath=..").locator("textarea").first
    if not ta_fr.count(): ta_fr = page.locator("textarea").first
    ta_fr.fill(consent.get("methode_fr", ""))

    ta_ar = page.locator("label:has-text('حدد كيفية أخذ الموافقة الصريحة')").locator("xpath=..").locator("textarea").first
    if not ta_ar.count() and page.locator("textarea").count() > 1:
        ta_ar = page.locator("textarea").nth(1)
    if ta_ar: ta_ar.fill(consent.get("methode_ar", ""))

    save_current_section(page, label="Consentement")
    print("✅ Consentement enregistré")

# ================== DROITS DES PERSONNES ==================

def fill_pair_ids(page, panel, fr_id: str, fr_val: str, ar_id: str | None, ar_val: str | None):
    fr_val = fr_val or ""; ar_val = ar_val if ar_val is not None else fr_val
    fr_nodes = _scope(panel, page, f'textarea#{fr_id}, input#{fr_id}')
    if fr_nodes.count():
        for i in range(fr_nodes.count()): safe_fill_input(fr_nodes.nth(i), fr_val)
    if ar_id:
        ar_nodes = _scope(panel, page, f'textarea#{ar_id}, input#{ar_id}')
        if ar_nodes.count():
            for i in range(ar_nodes.count()): safe_fill_input(ar_nodes.nth(i), ar_val)

def fill_bilingual_same_id(page, panel, base_id: str, fr_val: str, ar_val: str | None):
    fr_val = fr_val or ""; ar_val = ar_val if ar_val is not None else fr_val
    nodes = _scope(panel, page, f'textarea#{base_id}, input#{base_id}')
    cnt = nodes.count()
    if cnt >= 2:
        safe_fill_input(nodes.nth(0), fr_val); safe_fill_input(nodes.nth(1), ar_val)
    elif cnt == 1:
        safe_fill_input(nodes.first, fr_val if fr_val else ar_val)

def click_onglet_vuetify(page, titre: str, expect_prefix: str | None = None):
    variants = list(dict.fromkeys([titre, titre.replace("'", "’"), titre.replace("’", "'")]))
    tablist = page.locator('[role="tablist"]').first
    if tablist.count():
        for _ in range(10):
            for cand in variants:
                tab = tablist.get_by_role("tab", name=cand, exact=False).first
                if tab.count():
                    tab.scroll_into_view_if_needed(); tab.click(force=True)
                    page.wait_for_timeout(250)
                    if expect_prefix:
                        active = get_active_panel(page) or page
                        sel = active.locator(f'[id^="{expect_prefix}_"]')
                        if sel.count(): return
                    return
            nxt = tablist.locator('.v-slide-group__next')
            if nxt.count() and nxt.is_enabled(): nxt.click(); page.wait_for_timeout(150)
            else: break
    for cand in variants:
        t = page.get_by_role("tab", name=cand, exact=False).first
        if t.count(): t.click(force=True); page.wait_for_timeout(250); return
    page.get_by_text(titre.replace("’", "'"), exact=False).first.click(); page.wait_for_timeout(250)

def remplir_droits_personnes(page, dp):
    print("➡️ Section Droits des personnes")
    menu = page.get_by_text("Droit des personnes", exact=False)
    menu.scroll_into_view_if_needed(); menu.click(force=True)
    page.wait_for_load_state("networkidle"); page.wait_for_timeout(300)

    # Information
    if dp.get("information"):
        click_onglet_vuetify(page, "Droit à l'information", expect_prefix="information_right")
        panel = get_active_panel(page); info = dp["information"]; svc = info.get("service", {})
        fill_pair_ids(page, panel, "information_right_how", info.get("comment", ""), "information_right_how_ar", info.get("comment_ar"))
        fill_bilingual_same_id(page, panel, "information_right_mesures_prise", info.get("mesures", ""), info.get("mesures_ar"))
        fill_bilingual_same_id(page, panel, "information_right_service_name", svc.get("nom", ""), svc.get("nom_ar"))
        for fid, val in [("#information_right_phone", svc.get("mobile", "")), ("#information_right_email", svc.get("email","")),
                         ("#information_right_address", svc.get("adresse","")), ("#information_right_address_ar", svc.get("adresse_ar", svc.get("adresse","")))]:
            nodes = _scope(panel, page, fid)
            if nodes.count(): safe_fill_input(nodes.first, val)
        save_current_section(page, panel, label="Droit à l'information")

    # Accès / Rectification / Opposition
    def traiter_onglet(titre, pref, data):
        click_onglet_vuetify(page, titre, expect_prefix=pref)
        panel = get_active_panel(page); svc = data.get("service", {})
        fill_pair_ids(page, panel, f"{pref}_how", data.get("comment",""), f"{pref}_how_ar", data.get("comment_ar"))
        fill_bilingual_same_id(page, panel, f"{pref}_mesures_prise", data.get("mesures",""), data.get("mesures_ar"))
        fill_bilingual_same_id(page, panel, f"{pref}_service_name", svc.get("nom",""), svc.get("nom_ar"))
        for fid, val in [(f"#{pref}_phone", svc.get("mobile","")), (f"#{pref}_email", svc.get("email","")),
                         (f"#{pref}_address", svc.get("adresse","")), (f"#{pref}_address_ar", svc.get("adresse_ar", svc.get("adresse","")))]:
            nodes = _scope(panel, page, fid)
            if nodes.count(): safe_fill_input(nodes.first, val)
        save_current_section(page, panel, label=titre)

    if dp.get("acces"): traiter_onglet("Droit d'accès", "access_right", dp["acces"])
    if dp.get("rectification"): traiter_onglet("Droit à la rectification", "rectification_right", dp["rectification"])
    if dp.get("opposition"): traiter_onglet("Droit d'opposition", "opposition_right", dp["opposition"])
    print("✅ Droits des personnes complétés")

# ================== TÂCHES INITIALES ==================

def ajouter_taches_initiales(page, taches):
    print("➡️ Tâches initiales : ajout")
    menu = page.get_by_text("Tâches initiales", exact=False)
    menu.scroll_into_view_if_needed(); menu.click(force=True)
    page.wait_for_load_state("networkidle"); page.wait_for_timeout(300)

    for t in taches:
        page.get_by_role("button", name="Ajouter", exact=False).first.click()
        page.wait_for_timeout(300)
        modal = page.locator("div.v-overlay-container").last
        fields = modal.locator("input, textarea").filter(has_not=modal.locator('[aria-hidden="true"]'))
        fields.nth(0).fill(t.get("fr","")); fields.nth(1).fill(t.get("ar", t.get("fr","")))
        modal.locator("button:has-text('Enregistrer')").last.click()
        page.wait_for_timeout(400)

    save_current_section(page, label="Tâches initiales"); print("✅ Tâches initiales enregistrées")

# ================== SCRIPT PRINCIPAL ==================

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # ===== Connexion =====
    page.goto("https://admin.dp-manager.com/login")
    page.fill("input[placeholder=\"Nom d'utilisateur\"]", "admin")  # <-- modifie si besoin
    page.fill("input[type='password']", "Chtitha@58206670")         # <-- modifie si besoin
    page.click("button:has-text(\"S'authentifier\")")
    page.wait_for_url("**/tenants", timeout=20000)
    print("✅ Connexion réussie (page tenants)")

    # ===== Création traitement =====
    page.goto("https://admin.dp-manager.com/registers/trt-registers/create")
    page.wait_for_url("**/registers/trt-registers/create", timeout=20000)
    print("✅ Page création ouverte")

    page.fill("#code", "TRT-APP-SC")
    page.fill("#name", "Gestion des apprenants – sessions courtes")
    page.fill("#name_ar", "تسيير المتعلّمين – الدورات القصيرة")

    # Statut + Types
    page.click("#status"); page.click("text=En cours")
    page.click("label:has-text(\"Type de traitement\") + div")
    page.locator("div.v-overlay-container div.v-list-item-title", has_text="Manuel").first.click()
    page.locator("div.v-overlay-container div.v-list-item-title", has_text="Automatique").first.click()
    page.click("body")

    page.wait_for_selector("button[type='submit']:not([disabled])", timeout=5000)
    page.locator("button[type='submit']").click()

    # ===== Fondement légal =====
    page.click("text=Fondement légal d'un traitement")
    page.fill("textarea", "Loi n° 08-07, Ordonnance n° 05-07, Décret exécutif n° 04-90, Décret exécutif n° 23-130, Décret n° 22-208")
    page.locator("textarea").nth(1).fill("القانون رقم 08-07، الأمر رقم 05-07، المرسوم التنفيذي رقم 04-90، المرسوم التنفيذي رقم 23-130، المرسوم رقم 22-208")
    page.click("label:has-text('Le consentement exprès de la personne concernée')")
    page.click("label:has-text(\"L'exécution d'un contrat ou précontrat à la demande de la personne\")")
    page.locator("textarea").nth(2).fill("Exemple : protection des intérêts légitimes de l’organisation")
    save_current_section(page, label="Fondement légal")
    print("✅ Section Fondement légal enregistrée")

    # ===== Catégories de personnes =====
    menu_item = page.locator("text=Catégories de données à caractère personnel")
    menu_item.scroll_into_view_if_needed(); menu_item.click(force=True)
    page.wait_for_timeout(800)

    CATEGORIE_PERSONNE = "Apprenants"     # <-- EXACT libellé DP-Manager
    TYPE_COLLECTE = "Manuel et Automatique"
    MODE_COLLECTE = "Internet"           # <-- change par "Intranet" ou "Poste déconnecté" selon ta pratique

    page.get_by_role("button", name="Ajouter").click()
    page.wait_for_timeout(400)
    select_dropdown(page, "Catégorie des personnes concernées", CATEGORIE_PERSONNE)
    select_dropdown(page, "Type de collecte de données", TYPE_COLLECTE)
    select_dropdown(page, "Mode de collecte", MODE_COLLECTE)

    # (Sécurités optionnelles si présentes)
    for securite in ["Traçabilité", "Signature électronique", "Chiffrement", "Charte de sécurité"]:
        try:
            checkbox = page.locator(f"label:has-text('{securite}')")
            if checkbox.is_visible(): checkbox.click(); print(f"☑️ {securite} cochée")
        except: pass

    save_current_section(page, label=f"Catégorie {CATEGORIE_PERSONNE}")
    print("✅ Catégorie de personnes enregistrée")

    # ===== Catégories de données =====
    onglet_donnees = page.get_by_text("Catégorie des données collectées et traitées", exact=True)
    onglet_donnees.scroll_into_view_if_needed(); onglet_donnees.click(force=True)
    page.wait_for_timeout(800)

    categories_donnees = [
        # libellé EXACT + type EXACT (colonne 2 de ta base)
        {"categorie_label":"Nom et Prénom ..... اللقب والاسم","type":"Données perssonelles","origine":"Personne concernées","utilise":"Oui","source":"Formulaires en ligne","duree_type":"Limitée","duree":36,"declencheur":"Fin de la session"},
        {"categorie_label":"Date de Naissance ..... تاريخ الميلاد","type":"Données perssonelles","origine":"Personne concernées","utilise":"Oui","source":"Formulaires en ligne","duree_type":"Limitée","duree":36,"declencheur":"Fin de la session"},
        {"categorie_label":"Adresse Mail ..... البريد الإلكتروني","type":"Données perssonelles","origine":"Personne concernées","utilise":"Oui","source":"Formulaires en ligne","duree_type":"Limitée","duree":24,"declencheur":"Fin de la session"},
        {"categorie_label":"Nº de téléphone ..... رقم الهاتف","type":"Données perssonelles","origine":"Personne concernées","utilise":"Oui","source":"Formulaires en ligne","duree_type":"Limitée","duree":24,"declencheur":"Fin de la session"},
        {"categorie_label":"Données de pointage (présence) ..... بيانات الحضور","type":"Données professionnelles","origine":"Personne concernées","utilise":"Oui","source":"Système d'information","duree_type":"Limitée","duree":24,"declencheur":"Fin de la session"},
        {"categorie_label":"Résultats / Évaluation de fin de session","type":"Données professionnelles","origine":"Personne concernées","utilise":"Oui","source":"Système d'information","duree_type":"Limitée","duree":24,"declencheur":"Fin de la session"},
        {"categorie_label":"Numéro d’attestation / Détails de délivrance","type":"Données professionnelles","origine":"Personne concernées","utilise":"Oui","source":"Système d'information","duree_type":"Limitée","duree":36,"declencheur":"Fin de la session"},
        {"categorie_label":"Employeur ..... المستخدم","type":"Données professionnelles","origine":"Personne concernées","utilise":"Oui","source":"Justificatifs fournis","duree_type":"Limitée","duree":24,"declencheur":"Fin de la session"},
        {"categorie_label":"Organisme financeur","type":"Données financières","origine":"Personne concernées","utilise":"Oui","source":"Justificatifs fournis","duree_type":"Limitée","duree":24,"declencheur":"Fin de la session"},
        {"categorie_label":"Mode de paiement ..... وسيلة الدفع","type":"Données financières","origine":"Personne concernées","utilise":"Oui","source":"Système d'information","duree_type":"Limitée","duree":120,"declencheur":"Clôture de l’exercice comptable"},
        {"categorie_label":"Chèque barré ..... الصك المشطوب","type":"Données financières","origine":"Personne concernées","utilise":"Oui","source":"Dossiers papiers","duree_type":"Limitée","duree":120,"declencheur":"Clôture de l’exercice comptable"},
    ]
    for donnee in categories_donnees:
        ajouter_categorie_donnees(page, donnee)
    print("✅ Toutes les catégories de données ont été ajoutées")

    # ===== Finalité =====
    remplir_finalite(
        page,
        "Gestion administrative et pédagogique des apprenants inscrits à des sessions courtes : inscription, suivi de présence, évaluation et délivrance d’attestations de participation.",
        "التسيير الإداري والبيداغوجي للمتعلمين في الدورات القصيرة: التسجيل، متابعة الحضور، التقييم وإصدار شهادات المشاركة."
    )

    # ===== Sous-traitements (catalogue exhaustif ; supprime/commmente ce qui ne s'applique pas) =====
    onglet_sous_traitements = page.get_by_text("Sous-traitements", exact=True)
    onglet_sous_traitements.scroll_into_view_if_needed(); onglet_sous_traitements.click(force=True)
    page.wait_for_timeout(800)

    ST_BASE_CONTRAT = "L'exécution d'un contrat ou précontrat à la demande de la personne"
    ST_BASE_OBLIG = "Le respect d'une obligation légale."

    sous_traitements = [
        # 1) Collecte & inscription
        {"denomination_fr":"Remplissage de la fiche d’information","denomination_ar":"تعبئة استمارة المعلومات","types":["Manuel"],"base_legale":ST_BASE_CONTRAT,"note":"Saisie papier par personnel/assistant."},
        {"denomination_fr":"Formulaires d’inscription en ligne","denomination_ar":"استمارات التسجيل عبر الإنترنت","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Portail/LMS ou prestataire de formulaires."},
        {"denomination_fr":"Numérisation & OCR des pièces","denomination_ar":"رقمنة واستخلاص بيانات الوثائق","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Scan d’ID/diplômes/justificatifs."},
        {"denomination_fr":"Signature électronique (notice/consentement)","denomination_ar":"التوقيع الإلكتروني (المذكرة/الموافقة)","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Preuve de consentement."},
        {"denomination_fr":"Vérification d’identité (KYC allégé)","denomination_ar":"التحقق من الهوية","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Uniquement si nécessaire."},
        {"denomination_fr":"Prise de rendez-vous & agenda","denomination_ar":"حجز المواعيد وجدولة التسجيل","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Outil de booking."},

        # 2) Présence & organisation
        {"denomination_fr":"Remplissage de la feuille de présence","denomination_ar":"تعبئة ورقة الحضور","types":["Manuel"],"base_legale":ST_BASE_CONTRAT,"note":"Par agent/assistant."},
        {"denomination_fr":"Saisie des présences dans le SI","denomination_ar":"إدخال الحضور في النظام","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Back-office/ERP."},
        {"denomination_fr":"Contrôle de présence par QR/badge","denomination_ar":"التحقق من الحضور عبر QR/بطاقة","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Sans biométrie."},
        {"denomination_fr":"Planification des sessions & salles","denomination_ar":"تخطيط الجلسات والقاعات","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Outil de planning."},
        {"denomination_fr":"Convocations & rappels par e-mail (transactionnel)","denomination_ar":"الاستدعاءات والتذكيرات بالبريد","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"ESP/SMTP."},
        {"denomination_fr":"Rappels SMS/WhatsApp","denomination_ar":"تذكيرات عبر الرسائل القصيرة/واتساب","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Prestataire SMS."},

        # 3) Pédagogie, évaluation, certification
        {"denomination_fr":"Hébergement LMS & diffusion de contenus","denomination_ar":"استضافة المنصة التعليمية ونشر المحتوى","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"LMS hébergé."},
        {"denomination_fr":"Quizz & évaluations en ligne","denomination_ar":"اختبارات وتقييمات عبر الإنترنت","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Moteur d’évaluation."},
        {"denomination_fr":"Correction/notation assistée","denomination_ar":"تصحيح بمساعدة نظم","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Outils de correction."},
        {"denomination_fr":"Génération des attestations","denomination_ar":"إصدار الشهادات","types":["Automatique","Manuel"],"base_legale":ST_BASE_CONTRAT,"note":"Numérotation/édition PDF."},
        {"denomination_fr":"Archivage évaluations & attestations","denomination_ar":"أرشفة التقييمات والشهادات","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"Archivage/coffre-fort."},
        {"denomination_fr":"Visioconférence & webinaires","denomination_ar":"مؤتمرات مرئية وندوات","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Zoom/Meet/Teams."},
        {"denomination_fr":"Transcription pédagogique","denomination_ar":"نسخ المحتوى التعليمي","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Accessibilité (minimiser)."},
        {"denomination_fr":"Traduction de supports","denomination_ar":"ترجمة المحتويات","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Si nécessaire."},
        {"denomination_fr":"Anti-plagiat","denomination_ar":"مكافحة الانتحال","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Outil d’analyse."},
        {"denomination_fr":"Proctoring d’examen à distance","denomination_ar":"مراقبة الامتحانات عن بعد","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Intrusif : informer clairement."},

        # 4) Communication (hors transactionnel) — souvent traitement séparé
        {"denomination_fr":"E-mail marketing pour des formations","denomination_ar":"التسويق بالبريد لدورات","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Idéalement dans un traitement Marketing séparé."},
        {"denomination_fr":"Newsletter pédagogique","denomination_ar":"النشرة التعليمية","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Optionnel."},

        # 5) Paiement & administratif
        {"denomination_fr":"Paiement en ligne (inscription)","denomination_ar":"الدفع الإلكتروني للتسجيل","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"PSP ; pas de carte stockée localement."},
        {"denomination_fr":"Facturation & reçus","denomination_ar":"الفوترة والإيصالات","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"Outil comptable/ERP."},
        {"denomination_fr":"Remboursements & avoirs","denomination_ar":"الاسترجاعات والإشعارات الدائنة","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"PSP/ERP."},
        {"denomination_fr":"Comptabilité externalisée","denomination_ar":"المحاسبة لدى مزوّد خارجي","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"Cabinet comptable."},

        # 6) Formateur (sous-traitant)
        {"denomination_fr":"Animation pédagogique – Formateur externe","denomination_ar":"التنشيط البيداغوجي – مكوّن خارجي","types":["Manuel","Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Accès limité : listes, présences."},
        {"denomination_fr":"Évaluations & saisie des résultats – Formateur","denomination_ar":"التقييم وإدخال النتائج – المكوّن","types":["Manuel","Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Saisie/validation résultats."},
        {"denomination_fr":"Émission d’attestations – Formateur","denomination_ar":"إصدار الشهادات – المكوّن","types":["Automatique","Manuel"],"base_legale":ST_BASE_CONTRAT,"note":"Numérotation/édition PDF."},
        {"denomination_fr":"Hébergement LMS/visioconf opéré par le formateur","denomination_ar":"استضافة LMS/منصة مرئية يديرها المكوّن","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Si l’accès passe par son outil."},

        # 7) Partenaires privés (traités comme sous-traitants)
        {"denomination_fr":"Transmission à l’employeur (justificatifs)","denomination_ar":"مشاركة البيانات مع المستخدم","types":["Automatique","Manuel"],"base_legale":ST_BASE_CONTRAT,"note":"Présences/attestation minimales."},
        {"denomination_fr":"Transmission à l’organisme financeur","denomination_ar":"مشاركة البيانات مع الجهة الممولة","types":["Automatique","Manuel"],"base_legale":ST_BASE_CONTRAT,"note":"Justificatifs/factures."},

        # 8) Support & relation apprenant
        {"denomination_fr":"Helpdesk & tickets","denomination_ar":"مكتب المساعدة ونظام التذاكر","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Suivi des demandes."},
        {"denomination_fr":"Chat de support","denomination_ar":"دردشة المساندة","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Widget chat."},
        {"denomination_fr":"Sondages de satisfaction","denomination_ar":"استطلاعات الرضا","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Post-session."},

        # 9) Infrastructure & sécurité
        {"denomination_fr":"Hébergement cloud (appli & base)","denomination_ar":"الاستضافة السحابية للتطبيق والبيانات","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"IaaS/PaaS."},
        {"denomination_fr":"Sauvegarde & PRA externalisés","denomination_ar":"النسخ الاحتياطي وخطة التعافي","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"Backups chiffrés."},
        {"denomination_fr":"WAF/CDN/Anti-DDoS","denomination_ar":"جدار تطبيقات الويب وشبكات التوزيع","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"Protection périmétrique."},
        {"denomination_fr":"CAPTCHA/anti-spam","denomination_ar":"كابتشا ومضاد الرسائل المزعجة","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Protection des formulaires."},
        {"denomination_fr":"Supervision & logs","denomination_ar":"المراقبة والسجلات","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"Monitoring/centralisation."},
        {"denomination_fr":"Stockage documentaire (GED/Drive)","denomination_ar":"إدارة الوثائق والتخزين","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Dossiers/attestations."},
        {"denomination_fr":"Routage e-mail (SMTP relay)","denomination_ar":"توجيه البريد الإلكتروني","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Fournisseur SMTP."},
        {"denomination_fr":"Chiffrement & gestion de clés (KMS)","denomination_ar":"التشفير وإدارة المفاتيح","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"KMS externe."},
        {"denomination_fr":"Antivirus/EDR géré","denomination_ar":"مضاد فيروسات/حماية نقاط النهاية","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"Opérateur EDR."},
        {"denomination_fr":"SSO/Identity Provider","denomination_ar":"تسجيل الدخول الموحد","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Authentification unique."},
        {"denomination_fr":"Annuaire/AD/LDAP","denomination_ar":"الدليل المؤسسي","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Comptes & accès."},

        # 10) Conformité & cycle de vie
        {"denomination_fr":"Gestion des demandes de droits (DSAR)","denomination_ar":"إدارة طلبات الحقوق","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"Portail de requêtes."},
        {"denomination_fr":"Pseudonymisation/Anonymisation","denomination_ar":"إخفاء الهوية/تجريدها","types":["Automatique"],"base_legale":ST_BASE_CONTRAT,"note":"Stats/tests."},
        {"denomination_fr":"Journalisation & traçabilité","denomination_ar":"التسجيل والتتبع","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"Preuves d’accès/actions."},
        {"denomination_fr":"Destruction/suppression certifiée","denomination_ar":"حذف مُوثّق","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"Preuves d’effacement."},
        {"denomination_fr":"Audit de sécurité externe","denomination_ar":"تدقيق أمني خارجي","types":["Automatique"],"base_legale":ST_BASE_OBLIG,"note":"Rapports d’audit."},
    ]

    for st in sous_traitements:
        ajouter_sous_traitement(page, st)
    print("✅ Tous les sous-traitements ont été ajoutés")

    # ===== Conservation des données =====
    ajouter_conservation_donnees(page, {
        "modes":["Manuel","Informatique"],
        "informatique":{"nom":"Base Apprenants – Sessions courtes","lieu":"Serveur pédagogique de l’établissement (Algérie)"},
        "manuel":{"nom":"Dossiers Apprenants – Sessions courtes","lieu":"Archives scolarité (Algérie)"}
    })

    # ===== Destinataires (uniquement institutions de l'État de ta base) =====
    destinataires = [
        {"destinataire":"Direction de la formation professionnelle","moyen":"Connexion","cadre_legal":True,"objectifs":"Obligations/statistiques/homologation.","observation":"Transmission périodique via portail."},
        {"destinataire":"Ministère de la formation professionnelle","moyen":"Connexion","cadre_legal":True,"objectifs":"Suivi tutelle au niveau central.","observation":"Selon obligation."},
        {"destinataire":"Ministère de l'enseignement supérieur","moyen":"Connexion","cadre_legal":True,"objectifs":"Si l’établissement relève du MESRS.","observation":"Selon obligation."},
        {"destinataire":"L'adminsitration fiscale (Impôts)","moyen":"Connexion","cadre_legal":True,"objectifs":"Pièces comptables nominatives le cas échéant.","observation":"Via comptabilité."},
        {"destinataire":"Autorités judiciaires ou sécuritaires sur réquisition légale.","moyen":"Papier","cadre_legal":True,"objectifs":"Réquisition légale.","observation":"Transmission sur demande."},
        {"destinataire":"Les organismes et autorités compétents","moyen":"Papier","cadre_legal":True,"objectifs":"Obligations ponctuelles imposées par la tutelle.","observation":"Si applicable."}
    ]
    ajouter_destinataires(page, destinataires)

    # ===== Consentement =====
    ajouter_consentement(page, {
        "existe": True,
        "methode_fr": "Consentement explicite donné à l’inscription : signature de la notice d’information (papier ou signature électronique).",
        "methode_ar": "تُمنح الموافقة الصريحة عند التسجيل: التوقيع على مذكرة الإعلام (ورقية أو توقيع إلكتروني)."
    })

    # ===== Droits des personnes =====
    remplir_droits_personnes(page, {
        "information": {
            "comment": "Notice d’information remise à l’inscription + affichage sur le site.",
            "comment_ar": "مذكرة معلومات تُسلَّم عند التسجيل + عرض على الموقع.",
            "mesures": "Procédure interne et point de contact identifié (Scolarité).",
            "mesures_ar": "إجراء داخلي ونقطة اتصال محددة (مصلحة التمدرس).",
            "service": {"nom":"Service Scolarité","nom_ar":"مصلحة التمدرس","mobile":"0550123456","email":"scolarite@ecole.dz","adresse":"Accueil scolarité – Alger","adresse_ar":"استقبال التمدرس – الجزائر"}
        },
        "acces": {
            "comment": "Demande via formulaire en ligne ou guichet scolarité.",
            "comment_ar": "طلب عبر استمارة على الإنترنت أو لدى شباك التمدرس.",
            "mesures": "Vérification d’identité et réponse sous 30 jours.",
            "mesures_ar": "التحقق من الهوية والرد خلال 30 يومًا.",
            "service": {"nom":"Service Scolarité","nom_ar":"مصلحة التمدرس","mobile":"0551223344","email":"acces.donnees@ecole.dz","adresse":"Bureau scolarité – Bât. A","adresse_ar":"مكتب التمدرس – المبنى A"}
        },
        "rectification": {
            "comment": "Demande par e-mail ou formulaire dédié ; mise à jour sous 72 h.",
            "comment_ar": "طلب عبر البريد الإلكتروني أو استمارة مخصّصة؛ التحيين خلال 72 ساعة.",
            "mesures": "Workflow de correction validé par la scolarité.",
            "mesures_ar": "سير عمل للتصحيح بمصادقة مصلحة التمدرس.",
            "service": {"nom":"Service Scolarité","nom_ar":"مصلحة التمدرس","mobile":"0552667788","email":"rectification@ecole.dz","adresse":"Rez-de-chaussée, bâtiment A","adresse_ar":"الطابق الأرضي، المبنى A"}
        },
        "opposition": {
            "comment": "Formulaire d’opposition disponible en ligne (hors obligations légales).",
            "comment_ar": "استمارة اعتراض متاحة عبر الإنترنت (باستثناء الالتزامات القانونية).",
            "mesures": "Analyse de recevabilité et limitation du traitement concerné.",
            "mesures_ar": "تحليل قابلية القبول وتقييد المعالجة المعنية.",
            "service": {"nom":"DPO / Protection des données","nom_ar":"مسؤول حماية البيانات","mobile":"0553998877","email":"dpo@ecole.dz","adresse":"Direction – 2e étage","adresse_ar":"المديرية – الطابق الثاني"}
        }
    })

    # ===== Tâches initiales =====
    taches = [
        {"fr":"Informer les apprenants (notice FR/AR) et diffuser le lien de signature","ar":"إعلام المتعلّمين (مذكرة FR/AR) ونشر رابط التوقيع"},
        {"fr":"Collecter les consentements à l’inscription (papier ou e-signature)","ar":"جمع الموافقات عند التسجيل (ورقيًا أو توقيع إلكتروني)"},
        {"fr":"Mettre en place la procédure d’accès/rectification (formulaire + e-mail dédié)","ar":"وضع إجراء طلب الاطلاع/التصحيح (استمارة + بريد مخصّص)"},
        {"fr":"Vérifier et limiter les catégories de données aux besoins de la finalité","ar":"التحقق من فئات البيانات وحصرها بما يلزم لغرض المعالجة"}
    ]
    ajouter_taches_initiales(page, taches)

    print("🎉 Script terminé.")

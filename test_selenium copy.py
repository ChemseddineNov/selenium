from playwright.sync_api import sync_playwright

# --- Helpers génériques corrigés ---
def select_dropdown(page, label, value):
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
        el.fill(value)
        el.page.wait_for_timeout(120)
        return
    except Exception: pass
    try:
        el.click()
        el.page.keyboard.press("Control+A")
        el.type(value, delay=20)
    except Exception: pass
    el.page.wait_for_timeout(120)

def get_active_panel(page):
    pnl = page.locator('[role="tabpanel"]:visible, .v-window-item--active').first
    return pnl if pnl.count() else None

def _scope(panel_or_none, page, selector: str):
    if panel_or_none:
        nodes = panel_or_none.locator(selector)
        if nodes.count():
            return nodes
    return page.locator(selector)

def save_current_section(page, panel=None, label="section"):
    """Clique 'Enregistrer' de façon robuste (panel d'abord), gère overlays et attend networkidle."""
    for attempt in range(3):
        try:
            btns = _scope(panel, page, "button:has-text('Enregistrer')")
            btn = btns.filter(has_not=page.locator('[aria-hidden="true"]')).last
            if not btn.count():
                btn = page.locator("button:has-text('Enregistrer')").last
            btn.scroll_into_view_if_needed()
            btn.click(force=True)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(500)
            print(f"💾 Enregistré ({label})")
            return True
        except Exception:
            # si une liste/overlay intercepte → ESC puis retry
            try:
                if page.locator("div.v-overlay-container .v-list, div.v-overlay-container .v-overlay").filter(has_text="").first.is_visible():
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(200)
            except Exception:
                pass
            page.wait_for_timeout(400)
    print(f"⚠️ Impossible d'enregistrer ({label}), on continue quand même.")
    return False

# --- Ajout catégorie de données ---
def ajouter_categorie_donnees(page, donnee):
    print(f"➡️ Ajout en cours (Catégorie de données) : {donnee['categorie_index']} - {donnee['type']}")
    page.get_by_role("button", name="Ajouter").first.click()
    page.wait_for_timeout(1000)
    page.locator("label:has-text('Catégorie des données') + div input").click()
    page.wait_for_selector("div.v-overlay-container .v-list-item-title", state="visible")
    page.locator("div.v-overlay-container .v-list-item-title").nth(donnee["categorie_index"]).click()
    print(f"✅ Catégorie sélectionnée (index {donnee['categorie_index']})")
    select_dropdown(page, "Type des données", donnee["type"])
    select_dropdown(page, "Origine de la donnée", donnee["origine"])
    select_dropdown(page, "Utilisé(s) pour la finalité du traitement", donnee["utilise"])
    select_dropdown(page, "Source de données", donnee["source"])
    if donnee["duree_type"] != "Limitée":
        select_dropdown(page, "Durée de conservation", donnee["duree_type"])
    else:
        print("ℹ️ Durée de conservation par défaut = Limitée (aucune action nécessaire)")
    fill_input(page, "Préciser la durée (mois)", donnee["duree"])
    fill_input(page, "Élément déclencheur", donnee["declencheur"])
    save_current_section(page, label="Catégorie de données")
    print("✅ Catégorie de données ajoutée avec succès")

# --- Finalité ---
def remplir_finalite(page, finalite_fr, finalite_ar):
    print("➡️ Remplissage de la section Finalité")
    menu_item = page.get_by_text("Finalité", exact=True)
    menu_item.scroll_into_view_if_needed()
    menu_item.click(force=True)
    page.wait_for_timeout(1500)
    textarea_fr = page.locator("label:has-text('Finalité (but) du traitement')").locator("xpath=..").locator("textarea")
    textarea_fr.fill(finalite_fr)
    print(f"✅ Finalité FR remplie : {finalite_fr}")
    textarea_ar = page.locator("label:has-text('الغاية (الهدف) من المعالجة')").locator("xpath=..").locator("textarea")
    textarea_ar.fill(finalite_ar)
    print(f"✅ Finalité AR remplie : {finalite_ar}")
    save_current_section(page, label="Finalité")
    print("✅ Section Finalité enregistrée avec succès")

# --- Sous-traitement ---
def ajouter_sous_traitement(page, st):
    print(f"➡️ Ajout en cours (Sous-traitement) : {st['denomination_fr']} / {st['denomination_ar']}")
    page.get_by_role("button", name="Ajouter").first.click()
    page.wait_for_timeout(1000)
    modal = page.locator("div.v-overlay-container").last
    denom_fr = modal.locator("input").nth(0); denom_fr.wait_for(state="visible", timeout=5000); denom_fr.fill(st["denomination_fr"])
    print(f"✅ Dénomination FR remplie : {st['denomination_fr']}")
    denom_ar = modal.locator("input").nth(1); denom_ar.wait_for(state="visible", timeout=5000); denom_ar.fill(st["denomination_ar"])
    print(f"✅ Dénomination AR remplie : {st['denomination_ar']}")
    type_input = modal.locator("label:has-text('Type de traitement') + div input").first
    type_input.click()
    page.wait_for_selector("div.v-overlay-container .v-list-item-title", state="visible")
    for t in st["types"]:
        page.locator("div.v-overlay-container .v-list-item-title", has_text=t).first.click()
        print(f"✅ Type sélectionné : {t}")
    page.keyboard.press("Escape")
    select_dropdown(page, "Base légale", st["base_legale"])
    if st.get("sous_traitant"): select_dropdown(page, "Sous traitant", st["sous_traitant"])
    if st.get("logiciel"): select_dropdown(page, "Logiciel utilisé", st["logiciel"])
    modal.locator("textarea").last.fill(st["note"])
    print("✅ Note remplie")
    modal.locator("button:has-text('Enregistrer')").last.click()
    page.wait_for_timeout(1500)
    print("✅ Sous-traitement ajouté avec succès")

# --- Conservation des données ---
def ajouter_conservation_donnees(page, conservation):
    print("➡️ Ajout en cours (Conservation des données)")
    onglet = page.get_by_text("Conservation des données", exact=True)
    onglet.scroll_into_view_if_needed(); onglet.click(force=True)
    page.wait_for_load_state("networkidle"); page.wait_for_timeout(400)
    def fill_by_label(label_text: str, value: str):
        lab = page.locator(f"label:has-text('{label_text}')").first
        lab.wait_for(state="visible", timeout=10000)
        inp = lab.locator("xpath=..").locator("input, textarea").first
        inp.wait_for(state="visible", timeout=10000)
        inp.fill(value)
    def ensure_checked(name_substring: str):
        cb = page.get_by_role("checkbox", name=name_substring, exact=False).first
        cb.wait_for(state="visible", timeout=10000)
        try:
            if not cb.is_checked(): cb.check(force=True)
        except Exception: cb.click(force=True)
    if "Manuel" in conservation["modes"]: ensure_checked("Manuel"); print("☑️ Manuel coché")
    if "Informatique" in conservation["modes"]: ensure_checked("Informatique"); print("☑️ Informatique coché")
    if "informatique" in conservation:
        page.wait_for_selector("label:has-text('Nom de la base de données')", timeout=10000)
        fill_by_label("Nom de la base de données", conservation["informatique"]["nom"])
        fill_by_label("Lieu de stockage de la base de données", conservation["informatique"]["lieu"])
        print("✅ Conservation informatique remplie")
    if "manuel" in conservation:
        page.wait_for_selector("label:has-text('Nom du fichier manuel')", timeout=10000)
        fill_by_label("Nom du fichier manuel", conservation["manuel"]["nom"])
        fill_by_label("Lieu de stockage du fichier", conservation["manuel"]["lieu"])
        print("✅ Conservation manuelle remplie")
    save_current_section(page, label="Conservation des données")
    print("✅ Conservation des données enregistrée avec succès")

# === DESTINATAIRES ============================================================
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
    page.wait_for_timeout(400)
    modal = page.locator("div.v-overlay-container").last
    dest_input = modal.locator("label:has-text('Destinataire') + div input").first
    dest_input.click()
    if d.get("destinataire"):
        dest_input.fill(d["destinataire"]); modal.page.wait_for_timeout(300)
    modal.page.wait_for_selector("div.v-overlay-container .v-list-item-title", state="visible")
    modal.page.locator("div.v-overlay-container .v-list-item-title", has_text=d["destinataire"]).first.click()
    print(f"✅ Destinataire sélectionné : {d['destinataire']}")
    if d.get("moyen"): modal_select_dropdown(modal, "Moyen de communication", d["moyen"])
    if d.get("cadre_legal") is not None: modal_select_dropdown(modal, "Cadre legal", "Oui" if d["cadre_legal"] else "Non")
    if d.get("objectifs"): modal_fill(modal, "Objectifs", d["objectifs"])
    if d.get("observation"): modal_fill(modal, "Observation", d["observation"])
    modal.locator("button:has-text('Enregistrer')").last.click()
    page.wait_for_timeout(800)
    print("💾 Destinataire ajouté")

def ajouter_destinataires(page, items):
    print("➡️ Section Destinataires : ajout en cours")
    onglet = page.get_by_text("Les destinataires des données", exact=True)
    onglet.scroll_into_view_if_needed(); onglet.click(force=True)
    page.wait_for_timeout(800)
    for d in items:
        ajouter_un_destinataire(page, d)
    save_current_section(page, label="Destinataires")
    print("✅ Tous les destinataires ont été enregistrés")

# --- Consentement ---
def ajouter_consentement(page, consent):
    print("➡️ Ajout en cours (Consentement)")
    onglet = page.get_by_text("Consentement", exact=True)
    onglet.scroll_into_view_if_needed(); onglet.click(force=True)
    page.wait_for_timeout(800)
    select_dropdown(page, "Consentement des personnes concernées : Existe ?", "Oui" if consent.get("existe", True) else "Non")
    ta_fr = page.locator("label:has-text('Indiquer la méthode de consentement')").locator("xpath=..").locator("textarea").first
    if not ta_fr.count(): ta_fr = page.locator("textarea").first
    ta_fr.fill(consent.get("methode_fr", ""))
    ta_ar = page.locator("label:has-text('حدد كيفية أخذ الموافقة الصريحة')").locator("xpath=..").locator("textarea").first
    if not ta_ar.count():
        ta_ar = page.locator("textarea").nth(1) if page.locator("textarea").count() > 1 else None
    if ta_ar: ta_ar.fill(consent.get("methode_ar", ""))
    save_current_section(page, label="Consentement")
    print("✅ Consentement enregistré")

# ===================== DROITS DES PERSONNES — FR/AR ======================
def fill_pair_ids(page, panel, fr_id: str, fr_val: str, ar_id: str | None, ar_val: str | None):
    fr_val = fr_val or ""
    ar_val = ar_val if ar_val is not None else fr_val
    fr_nodes = _scope(panel, page, f'textarea#{fr_id}, input#{fr_id}')
    if fr_nodes.count():
        print(f"   📝 FR -> #{fr_id}")
        for i in range(fr_nodes.count()):
            safe_fill_input(fr_nodes.nth(i), fr_val)
    else:
        print(f"   ⚠️ FR introuvable: #{fr_id}")
    if ar_id:
        ar_nodes = _scope(panel, page, f'textarea#{ar_id}, input#{ar_id}')
        if ar_nodes.count():
            print(f"   📝 AR -> #{ar_id}")
            for i in range(ar_nodes.count()):
                safe_fill_input(ar_nodes.nth(i), ar_val)
        else:
            print(f"   ⚠️ AR introuvable: #{ar_id}")

def fill_bilingual_same_id(page, panel, base_id: str, fr_val: str, ar_val: str | None):
    fr_val = fr_val or ""
    ar_val = ar_val if ar_val is not None else fr_val
    nodes = _scope(panel, page, f'textarea#{base_id}, input#{base_id}')
    cnt = nodes.count()
    if cnt >= 2:
        print(f"   📝 FR/AR -> #{base_id} (doublon x{cnt})")
        safe_fill_input(nodes.nth(0), fr_val)
        safe_fill_input(nodes.nth(1), ar_val)
    elif cnt == 1:
        print(f"   📝 FR -> #{base_id} (unique)")
        safe_fill_input(nodes.first, fr_val if fr_val else ar_val)
    else:
        print(f"   ⚠️ Champ introuvable: #{base_id}")

def click_onglet_vuetify(page, titre: str, expect_prefix: str | None = None):
    def variants(t):
        return list(dict.fromkeys([t, t.replace("'", "’"), t.replace("’", "'")]))
    tablist = page.locator('[role="tablist"]').first
    if tablist.count():
        next_btn = tablist.locator('.v-slide-group__next')
        prev_btn = tablist.locator('.v-slide-group__prev')
        for _ in range(12):
            for cand in variants(titre):
                tab = tablist.get_by_role("tab", name=cand, exact=False).first
                if tab.count():
                    try: tab.scroll_into_view_if_needed()
                    except Exception: pass
                    tab.click(force=True)
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(300)
                    if expect_prefix:
                        panel = get_active_panel(page) or page
                        try:
                            (panel if hasattr(panel, "locator") else page).locator(f'[id^="{expect_prefix}_"]').first.wait_for(timeout=1500)
                        except Exception:
                            pass
                    return
            if next_btn.count() and next_btn.is_enabled():
                try: next_btn.click(); page.wait_for_timeout(200)
                except Exception: break
            else: break
        for _ in range(6):
            if prev_btn.count() and prev_btn.is_enabled():
                prev_btn.click(); page.wait_for_timeout(200)
    for cand in variants(titre):
        t = page.get_by_role("tab", name=cand, exact=False).first
        if t.count():
            t.click(force=True); page.wait_for_timeout(300); return
    page.get_by_text(titre.replace("’", "'"), exact=False).first.click(); page.wait_for_timeout(300)

def remplir_droits_personnes(page, dp):
    print("➡️ Remplissage de la section Droits des personnes")
    menu = page.get_by_text("Droit des personnes", exact=False)
    menu.scroll_into_view_if_needed(); menu.click(force=True)
    page.wait_for_load_state("networkidle"); page.wait_for_timeout(400)

    # ---- Onglet 1 : Droit à l'information ----
    if dp.get("information"):
        click_onglet_vuetify(page, "Droit à l'information", expect_prefix="information_right")
        panel = get_active_panel(page)
        info = dp["information"]; svc = info.get("service", {})

        fill_pair_ids(page, panel, "information_right_how", info.get("comment", ""), "information_right_how_ar", info.get("comment_ar"))
        fill_bilingual_same_id(page, panel, "information_right_mesures_prise", info.get("mesures", ""), info.get("mesures_ar"))
        ar_m = _scope(panel, page, "#information_right_mesures_prise_ar")
        if ar_m.count(): safe_fill_input(ar_m.first, info.get("mesures_ar", info.get("mesures", "")))
        # service FR/AR
        fill_bilingual_same_id(page, panel, "information_right_service_name", svc.get("nom", ""), svc.get("nom_ar"))
        fill_pair_ids(page, panel, "information_right_service_name", svc.get("nom", ""), "information_right_service_name_ar", svc.get("nom_ar"))
        # contacts
        mob = _scope(panel, page, "#information_right_phone")
        if mob.count(): safe_fill_input(mob.first, svc.get("mobile", ""))
        email = _scope(panel, page, "#information_right_email")
        if email.count(): safe_fill_input(email.first, svc.get("email", ""))
        # adresses
        addr_fr = _scope(panel, page, "#information_right_address")
        if addr_fr.count(): safe_fill_input(addr_fr.first, svc.get("adresse", ""))
        else:
            alt_fr = _scope(panel, page, 'input[placeholder*="Adresse"]').first
            if alt_fr.count(): safe_fill_input(alt_fr, svc.get("adresse", ""))
        addr_ar = _scope(panel, page, "#information_right_address_ar")
        if addr_ar.count(): safe_fill_input(addr_ar.first, svc.get("adresse_ar", svc.get("adresse", "")))
        # justification (si présente)
        if svc.get("justification"):
            try: _scope(panel, page, "fieldset textarea").first.fill(svc["justification"])
            except Exception:
                try:
                    lab = _scope(panel, page, 'label:has-text("Justification")').first
                    lab.locator("xpath=..").locator("textarea, input").first.fill(svc["justification"])
                except Exception: pass

        # ✅ ENREGISTRER AVANT DE PASSER AU 2e ONGLET
        save_current_section(page, panel, label="Droit à l'information")
        print("✅ Onglet 'Droit à l'information' enregistré")

    # ---- Fonctions de fallback libellé/placeholder (inchangées) ----
    def fill_area_by_label_in(panel, label_txt, value):
        if not value: return
        lab = _scope(panel, page, f'label:has-text("{label_txt}")').first
        if lab.count():
            area = lab.locator("xpath=..").locator("textarea, input").first
            safe_fill_input(area, value)

    def fill_service_block_generic(panel, service):
        try:
            if service.get("nom"):
                _scope(panel, page, 'input[placeholder*="nom du service"]').first.fill(service["nom"])
        except Exception: pass
        try:
            if service.get("justification"):
                _scope(panel, page, "fieldset textarea").first.fill(service["justification"])
        except Exception: pass
        try:
            if service.get("mobile"):
                _scope(panel, page, 'input[placeholder*="Mobile"]').first.fill(service["mobile"])
        except Exception: pass
        try:
            if service.get("email"):
                _scope(panel, page, 'input[placeholder*="E-mail"]').first.fill(service["email"])
        except Exception: pass
        try:
            if service.get("adresse"):
                _scope(panel, page, 'input[placeholder*="Adresse"]').first.fill(service["adresse"])
        except Exception: pass

    def traiter_autre_onglet(titre, data):
        prefix_map = {
            "Droit d'accès": "access_right",
            "Droit à la rectification": "rectification_right",
            "Droit d'opposition": "opposition_right",
        }
        pref = prefix_map.get(titre)
        click_onglet_vuetify(page, titre, expect_prefix=pref or "")
        panel = get_active_panel(page)

        if pref:
            fill_pair_ids(page, panel, f"{pref}_how", data.get("comment", ""), f"{pref}_how_ar", data.get("comment_ar"))
            fill_bilingual_same_id(page, panel, f"{pref}_mesures_prise", data.get("mesures", ""), data.get("mesures_ar"))
            ar_node = _scope(panel, page, f"#{pref}_mesures_prise_ar")
            if ar_node.count():
                safe_fill_input(ar_node.first, data.get("mesures_ar", data.get("mesures", "")))

        # Fallback libellés/placeholder
        fill_area_by_label_in(panel, "Comment les personnes sont-elles informées", data.get("comment", ""))
        fill_area_by_label_in(panel, "Quelles sont les mesures prises pour faciliter l'exercice", data.get("mesures", ""))
        fill_service_block_generic(panel, data.get("service", {}))

        save_current_section(page, panel, label=titre)
        print(f"✅ Onglet '{titre}' enregistré")

    # ---- Onglets 2 → 4 ----
    if dp.get("acces"): traiter_autre_onglet("Droit d'accès", dp["acces"])
    if dp.get("rectification"): traiter_autre_onglet("Droit à la rectification", dp["rectification"])
    if dp.get("opposition"): traiter_autre_onglet("Droit d'opposition", dp["opposition"])

    print("✅ Section Droits des personnes complétée")

# =================== FIN DROITS (reste du script inchangé) ===================

# --- Script principal ---
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # Login
    page.goto("https://admin.dp-manager.com/login")
    page.fill("input[placeholder=\"Nom d'utilisateur\"]", "admin")
    page.fill("input[type='password']", "Chtitha@58206670")
    page.click("button:has-text(\"S'authentifier\")")
    page.wait_for_url("**/tenants", timeout=20000)
    print("✅ Connexion réussie (page tenants)")

    # Création traitement
    page.goto("https://admin.dp-manager.com/registers/trt-registers/create")
    page.wait_for_url("**/registers/trt-registers/create", timeout=20000)
    print("✅ Page création ouverte")

    page.fill("#code", "TRT-TEST1")
    page.fill("#name", "Test Ressources Humaines")
    page.fill("#name_ar", "تجربة الموارد البشرية")

    page.click("#status")
    page.click("text=En cours")

    page.click("label:has-text(\"Type de traitement\") + div")
    page.locator("div.v-overlay-container div.v-list-item-title", has_text="Manuel").first.click()
    page.locator("div.v-overlay-container div.v-list-item-title", has_text="Automatique").first.click()
    page.click("body")

    save_button = page.locator("button[type='submit']")
    page.wait_for_selector("button[type='submit']:not([disabled])", timeout=5000)
    save_button.click()

    # Fondement légal
    page.click("text=Fondement légal d'un traitement")
    page.fill("textarea", "Loi n° 08-07, Ordonnance n° 05-07, Décret exécutif n° 04-90, Décret exécutif n° 23-130, Décret n° 22-208")
    page.locator("textarea").nth(1).fill("القانون رقم 08-07، الأمر رقم 05-07، المرسوم التنفيذي رقم 04-90، المرسوم التنفيذي رقم 23-130، المرسوم رقم 22-208")
    page.click("label:has-text('Le consentement exprès de la personne concernée')")
    page.click("label:has-text(\"L'exécution d'un contrat ou précontrat à la demande de la personne\")")
    page.locator("textarea").nth(2).fill("Exemple : protection des intérêts légitimes de l’organisation")
    save_current_section(page, label="Fondement légal")
    print("✅ Section Fondement légal enregistrée")

    # Catégories de personnes
    menu_item = page.locator("text=Catégories de données à caractère personnel")
    menu_item.scroll_into_view_if_needed()
    menu_item.click(force=True)
    page.wait_for_timeout(2000)

    categories_personnes = ["Adhérant", "Salariés"]
    type_collecte = "Manuel et Automatique"
    mode_collecte = "Internet"

    for categorie_personne in categories_personnes:
        page.get_by_role("button", name="Ajouter").click()
        page.wait_for_timeout(1000)
        select_dropdown(page, "Catégorie des personnes concernées", categorie_personne)
        select_dropdown(page, "Type de collecte de données", type_collecte)
        select_dropdown(page, "Mode de collecte", mode_collecte)
        for securite in ["Traçabilité", "Signature électronique", "Chiffrement", "Charte de sécurité"]:
            try:
                checkbox = page.locator(f"label:has-text('{securite}')")
                if checkbox.is_visible():
                    checkbox.click()
                    print(f"☑️ {securite} cochée")
            except: pass
        save_current_section(page, label=f"Catégorie {categorie_personne}")
        page.wait_for_timeout(1500)

    print("✅ Toutes les catégories de personnes ont été ajoutées avec succès")

    # Catégories de données
    onglet_donnees = page.get_by_text("Catégorie des données collectées et traitées", exact=True)
    onglet_donnees.scroll_into_view_if_needed()
    onglet_donnees.click(force=True)
    page.wait_for_timeout(1500)

    categories_donnees = [
        {"categorie_index": 0, "type": "Nom et Prénom", "origine": "Personne concernées", "utilise": "Oui", "source": "Dossiers papiers", "duree_type": "Limitée", "duree": 120, "declencheur": "A partir de la fin du contrat"},
        {"categorie_index": 0, "type": "Date de Naissance", "origine": "Personne concernées", "utilise": "Oui", "source": "Dossiers papiers", "duree_type": "Limitée", "duree": 120, "declencheur": "A partir de la fin du contrat"}
    ]
    for donnee in categories_donnees:
        ajouter_categorie_donnees(page, donnee)
    print("✅ Toutes les catégories de données ont été ajoutées avec succès")

    # Finalité
    remplir_finalite(
        page,
        "Gestion administrative et pédagogique des enseignants et formateurs dans le cadre des activités de l’établissement de formation",
        "التسيير الإداري والبيداغوجي للمعلمين والمكونين في إطار نشاطات مؤسسة التكوين"
    )

    # Sous-traitements
    onglet_sous_traitements = page.get_by_text("Sous-traitements", exact=True)
    onglet_sous_traitements.scroll_into_view_if_needed(); onglet_sous_traitements.click(force=True)
    page.wait_for_timeout(1500)
    sous_traitements = [
        {"denomination_fr": "Paie externalisée","denomination_ar": "إدارة الأجور","types": ["Manuel","Automatique"],"base_legale": "Le respect d'une obligation légale.","sous_traitant": "Comptable externe","logiciel": "Novoreka","note": "Gestion de la paie via prestataire externe"},
        {"denomination_fr": "Audit externe","denomination_ar": "مراجعة خارجية","types": ["Automatique"],"base_legale": "L'exécution d'une mission d'intérêt public.","sous_traitant": "Auditeur externe","logiciel": "","note": "Audit annuel obligatoire"}
    ]
    for st in sous_traitements:
        ajouter_sous_traitement(page, st)
    print("✅ Tous les sous-traitements ont été ajoutés avec succès")

    # Conservation des données
    ajouter_conservation_donnees(page, {
        "modes": ["Manuel", "Informatique"],
        "informatique": {"nom": "Fichier des enseignants et formateurs","lieu": "Serveur au siège de l'école (Algérie)"},
        "manuel": {"nom": "Dossiers des enseignants et formateurs","lieu": "Salle d'archive au siège de l'école (Algérie)"}
    })

    # Destinataires
    destinataires = [
        {"destinataire": "CNAS","moyen": "Connexion","cadre_legal": True,"objectifs": "Déclarations sociales et vérifications.","observation": "Transmission mensuelle via portail."},
        {"destinataire": "Inspection de travail","moyen": "Papier","cadre_legal": True,"objectifs": "Contrôle réglementaire.","observation": "Envoi sur demande."}
    ]
    ajouter_destinataires(page, destinataires)

    ajouter_consentement(page, {
        "existe": True,
        "methode_fr": "Consentement explicite écrit collecté via formulaire signé (papier ou signature électronique).",
        "methode_ar": "موافقة صريحة مكتوبة يتم جمعها عبر استمارة ممضاة (ورقية أو توقيع إلكتروني)."
    })

   # Droits des personnes (FR + AR)
    remplir_droits_personnes(page, {
    "information": {
        "comment": "Affichage sur le site et note d’information remise lors de l’inscription.",
        "comment_ar": "عرض على الموقع ومذكرة معلومات تُسلَّم عند التسجيل.",
        "mesures": "Procédures internes + contact dédié au sein du service juridique.",
        "mesures_ar": "إجراءات داخلية + جهة اتصال مخصصة ضمن المصلحة القانونية.",
        "service": {
            "nom": "Service Juridique", "nom_ar": "المصلحة القانونية",
            "justification": "Point de contact pour toute demande relative à l'information.",
            "mobile": "0550123456", "email": "juridique@ecole.dz",
            "adresse": "Siège de l'école – Alger", "adresse_ar": "مقر المدرسة – الجزائر"
        }
    },
    "acces": {
        "comment": "Formulaire de demande en ligne + accueil physique.", "comment_ar": "استمارة طلب عبر الإنترنت + استقبال حضوري.",
        "mesures": "Vérification d’identité et réponse sous 30 jours.", "mesures_ar": "التحقق من الهوية والرد خلال 30 يومًا.",
        "service": {
            "nom": "Service Archives", "nom_ar": "مصلحة الأرشيف",
            "mobile": "0551223344", "email": "archives@ecole.dz",
            "adresse": "Bureau des archives – Alger", "adresse_ar": "مكتب الأرشيف – الجزائر"
        }
    },
    "rectification": {
        "comment": "Demande via e-mail ou guichet administratif.", "comment_ar": "طلب عبر البريد الإلكتروني أو الشباك الإداري.",
        "mesures": "Procédure de correction dans 72 h.", "mesures_ar": "إجراء التصحيح خلال 72 ساعة.",
        "service": {
            "nom": "Service Scolarité", "nom_ar": "مصلحة التمدرس",
            "mobile": "0552667788", "email": "scolarite@ecole.dz",
            "adresse": "Rez-de-chaussée, bâtiment A", "adresse_ar": "الطابق الأرضي، المبنى A"
        }
    },
    "opposition": {
        "comment": "Formulaire d’opposition disponible sur le site.", "comment_ar": "استمارة اعتراض متاحة على الموقع.",
        "mesures": "Analyse de recevabilité et désactivation des traitements concernés.", "mesures_ar": "تحليل قابلية القبول وإيقاف المعالجات المعنية.",
        "service": {
            "nom": "DPO / Protection des données", "nom_ar": "مسؤول حماية البيانات",
            "mobile": "0553998877", "email": "dpo@ecole.dz",
            "adresse": "Direction – 2e étage", "adresse_ar": "المديرية – الطابق الثاني"
        }
    }
})

from playwright.sync_api import sync_playwright

# --- Helpers génériques corrigés ---
def select_dropdown(page, label, value):
    # cibler uniquement l'input visible (celui qui a un placeholder)
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


# --- Ajout catégorie de données ---
def ajouter_categorie_donnees(page, donnee):
    print(f"➡️ Ajout en cours (Catégorie de données) : {donnee['categorie_index']} - {donnee['type']}")

    page.get_by_role("button", name="Ajouter").first.click()
    page.wait_for_timeout(1000)

    # Catégorie
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

    page.locator("button:has-text('Enregistrer')").last.click()
    page.wait_for_timeout(1500)
    print(f"✅ Catégorie de données ajoutée avec succès")


# --- Remplir Finalité ---
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

    page.locator("button:has-text('Enregistrer')").last.click()
    page.wait_for_timeout(1500)
    print("✅ Section Finalité enregistrée avec succès")


# --- Ajout Sous-traitement ---
def ajouter_sous_traitement(page, st):
    print(f"➡️ Ajout en cours (Sous-traitement) : {st['denomination_fr']} / {st['denomination_ar']}")

    page.get_by_role("button", name="Ajouter").first.click()
    page.wait_for_timeout(1000)

    modal = page.locator("div.v-overlay-container").last

    # --- Champ FR ---
    denom_fr = modal.locator("input").nth(0)
    denom_fr.wait_for(state="visible", timeout=5000)
    denom_fr.fill(st["denomination_fr"])
    print(f"✅ Dénomination FR remplie : {st['denomination_fr']}")

    # --- Champ AR ---
    denom_ar = modal.locator("input").nth(1)
    denom_ar.wait_for(state="visible", timeout=5000)
    denom_ar.fill(st["denomination_ar"])
    print(f"✅ Dénomination AR remplie : {st['denomination_ar']}")

    # --- Type de traitement (multi-select) ---
    type_input = modal.locator("label:has-text('Type de traitement') + div input").first
    type_input.click()
    page.wait_for_selector("div.v-overlay-container .v-list-item-title", state="visible")

    for t in st["types"]:
        option = page.locator("div.v-overlay-container .v-list-item-title", has_text=t).first
        option.click()
        print(f"✅ Type sélectionné : {t}")

    page.keyboard.press("Escape")  # ferme le menu après toutes les sélections

    # --- Base légale ---
    select_dropdown(page, "Base légale", st["base_legale"])

    # --- Sous-traitant ---
    if st.get("sous_traitant"):
        select_dropdown(page, "Sous traitant", st["sous_traitant"])

    # --- Logiciel ---
    if st.get("logiciel"):
        select_dropdown(page, "Logiciel utilisé", st["logiciel"])

    # --- Note ---
    modal.locator("textarea").last.fill(st["note"])
    print("✅ Note remplie")

    # --- Enregistrer ---
    modal.locator("button:has-text('Enregistrer')").last.click()
    page.wait_for_timeout(1500)
    print("✅ Sous-traitement ajouté avec succès")


# --- Conservation des données (robuste) ---
def ajouter_conservation_donnees(page, conservation):
    print("➡️ Ajout en cours (Conservation des données)")

    # Aller dans l'onglet
    onglet = page.get_by_text("Conservation des données", exact=True)
    onglet.scroll_into_view_if_needed()
    onglet.click(force=True)

    # laisser la vue se stabiliser
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(400)

    # Helper local pour remplir par label
    def fill_by_label(label_text: str, value: str):
        lab = page.locator(f"label:has-text('{label_text}')").first
        lab.wait_for(state="visible", timeout=10000)
        inp = lab.locator("xpath=..").locator("input, textarea").first
        inp.wait_for(state="visible", timeout=10000)
        inp.fill(value)

    # Cocher via rôle aria (plus robuste que le :has-text bilingue)
    def ensure_checked(name_substring: str):
        cb = page.get_by_role("checkbox", name=name_substring, exact=False).first
        cb.wait_for(state="visible", timeout=10000)
        try:
            if not cb.is_checked():
                cb.check(force=True)
        except Exception:
            cb.click(force=True)

    # Coche les modes demandés
    if "Manuel" in conservation["modes"]:
        ensure_checked("Manuel")
        print("☑️ Manuel coché")

    if "Informatique" in conservation["modes"]:
        ensure_checked("Informatique")
        print("☑️ Informatique coché")

    # Remplissage des blocs
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

    # Enregistrer
    save_btn = page.locator("button:has-text('Enregistrer')").last
    save_btn.scroll_into_view_if_needed()
    save_btn.click(force=True)
    page.wait_for_timeout(1000)
    print("✅ Conservation des données enregistrée avec succès")


# === DESTINATAIRES ============================================================
# Helpers portés sur la modale
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
    # Ouvrir la modale
    page.get_by_role("button", name="Ajouter").first.click()
    page.wait_for_timeout(400)
    modal = page.locator("div.v-overlay-container").last

    # Destinataire (lookup)
    dest_input = modal.locator("label:has-text('Destinataire') + div input").first
    dest_input.click()
    if d.get("destinataire"):
        dest_input.fill(d["destinataire"])
        modal.page.wait_for_timeout(300)
    modal.page.wait_for_selector("div.v-overlay-container .v-list-item-title", state="visible")
    modal.page.locator("div.v-overlay-container .v-list-item-title", has_text=d["destinataire"]).first.click()
    print(f"✅ Destinataire sélectionné : {d['destinataire']}")

    # Moyen de communication
    if d.get("moyen"):
        modal_select_dropdown(modal, "Moyen de communication", d["moyen"])

    # Cadre legal (Oui/Non)
    if d.get("cadre_legal") is not None:
        modal_select_dropdown(modal, "Cadre legal", "Oui" if d["cadre_legal"] else "Non")

    # Objectifs / Observation
    if d.get("objectifs"):
        modal_fill(modal, "Objectifs", d["objectifs"])
    if d.get("observation"):
        modal_fill(modal, "Observation", d["observation"])

    # Enregistrer
    modal.locator("button:has-text('Enregistrer')").last.click()
    page.wait_for_timeout(800)
    print("💾 Destinataire ajouté")

def ajouter_destinataires(page, items):
    print("➡️ Section Destinataires : ajout en cours")
    onglet = page.get_by_text("Les destinataires des données", exact=True)
    onglet.scroll_into_view_if_needed()
    onglet.click(force=True)
    page.wait_for_timeout(800)

    for d in items:
        ajouter_un_destinataire(page, d)

    # Enregistrer la section
    save = page.locator("button:has-text('Enregistrer')").last
    save.scroll_into_view_if_needed()
    save.click()
    page.wait_for_timeout(1200)
    print("✅ Tous les destinataires ont été enregistrés")
# ============================================================================
# --- Consentement ---
def ajouter_consentement(page, consent):
    """
    consent = {
        "existe": True/False,
        "methode_fr": "…",
        "methode_ar": "…"
    }
    """
    print("➡️ Ajout en cours (Consentement)")

    # Ouvrir l'onglet
    onglet = page.get_by_text("Consentement", exact=True)
    onglet.scroll_into_view_if_needed()
    onglet.click(force=True)
    page.wait_for_timeout(800)

    # Oui / Non
    select_dropdown(
        page,
        "Consentement des personnes concernées : Existe ?",
        "Oui" if consent.get("existe", True) else "Non",
    )

    # Textarea FR (libellé FR ou fallback premier textarea)
    ta_fr = page.locator("label:has-text('Indiquer la méthode de consentement')").locator("xpath=..").locator("textarea").first
    if not ta_fr.count():
        ta_fr = page.locator("textarea").first
    ta_fr.fill(consent.get("methode_fr", ""))

    # Textarea AR (libellé AR ou fallback deuxième textarea s’il existe)
    ta_ar = page.locator("label:has-text('حدد كيفية أخذ الموافقة الصريحة')").locator("xpath=..").locator("textarea").first
    if not ta_ar.count():
        # s'il n'y a qu'une seule zone, on ne fait rien ; s'il y en a 2, on prend la seconde
        if page.locator("textarea").count() > 1:
            ta_ar = page.locator("textarea").nth(1)
        else:
            ta_ar = None
    if ta_ar:
        ta_ar.fill(consent.get("methode_ar", ""))

    # Enregistrer
    page.locator("button:has-text('Enregistrer')").last.click()
    page.wait_for_timeout(800)
    print("✅ Consentement enregistré")
    
    # --- DROITS DES PERSONNES ----------------------------------------------------
def remplir_droits_personnes(page, dp):
    print("➡️ Remplissage de la section Droits des personnes")

    # Aller à la section
    menu = page.get_by_text("Droit des personnes", exact=False)
    menu.scroll_into_view_if_needed()
    menu.click(force=True)
    page.wait_for_timeout(800)

    # Helpers
    def click_onglet(nom):
        try:
            tab = page.get_by_role("tab", name=nom, exact=False).first
            tab.wait_for(state="visible", timeout=5000)
            tab.click(force=True)
        except Exception:
            page.get_by_text(nom, exact=False).first.click()
        page.wait_for_timeout(400)

    def fill_area_by_label(label_txt, value):
        if not value:
            return
        # ⚠️ utiliser des guillemets doubles dans has-text pour éviter le conflit avec l'apostrophe
        lab = page.locator(f'label:has-text("{label_txt}")').first
        lab.wait_for(state="visible", timeout=8000)
        area = lab.locator("xpath=..").locator("textarea, input").first
        area.wait_for(state="visible", timeout=8000)
        area.fill(value)

    def fill_service_block(service):
        if service.get("nom"):
            page.get_by_placeholder("Le nom du service auprès duquel la personne concernée").first.fill(service["nom"])
        if service.get("justification"):
            # 1er textarea du bloc service (fallback si structure varie)
            zone = page.locator("fieldset textarea").first
            zone.fill(service["justification"])
        if service.get("mobile"):
            page.get_by_placeholder("Mobile").first.fill(service["mobile"])
        if service.get("email"):
            page.get_by_placeholder("E-mail").first.fill(service["email"])
        if service.get("adresse"):
            page.get_by_placeholder("Adresse").first.fill(service["adresse"])

    def traiter_un_onglet(titre, data):
        click_onglet(titre)
        fill_area_by_label("Comment les personnes sont-elles informées", data.get("comment", ""))
        # Cette étiquette contient l'apostrophe → guillemets doubles indispensables
        fill_area_by_label("Quelles sont les mesures prises pour faciliter l'exercice", data.get("mesures", ""))
        fill_service_block(data.get("service", {}))
        save_btn = page.locator("button:has-text('Enregistrer')").last
        save_btn.scroll_into_view_if_needed()
        save_btn.click(force=True)
        page.wait_for_timeout(600)
        print(f"✅ Onglet '{titre}' enregistré")

    if dp.get("information"):
        traiter_un_onglet("Droit à l'information", dp["information"])
    if dp.get("acces"):
        traiter_un_onglet("Droit d'accès", dp["acces"])
    if dp.get("rectification"):
        traiter_un_onglet("Droit à la rectification", dp["rectification"])
    if dp.get("opposition"):
        traiter_un_onglet("Droit d'opposition", dp["opposition"])

    print("✅ Section Droits des personnes complétée")




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

    page.fill("#code", "TRT-TEST")
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

    
    remplir_droits_personnes(page, {
    "information": {
        "comment": "Affichage sur le site et note d’information remise lors de l’inscription.",
        "comment_ar": "عرض على الموقع ومذكرة معلومات تُسلَّم عند التسجيل.",
        "mesures": "Procédures internes + contact dédié au sein du service juridique.",
        "mesures_ar": "إجراءات داخلية + جهة اتصال مخصصة ضمن المصلحة القانونية.",
        "service": {
            "nom": "Service Juridique",
            "nom_ar": "المصلحة القانونية",
            "justification": "Point de contact pour toute demande relative à l'information.",
            # "justification_ar": "نقطة اتصال لأي طلب متعلق بالمعلومة.",  # décommente si un champ existe
            "mobile": "0550 12 34 56",
            "mobile_ar": "0550 12 34 56",
            "email": "juridique@ecole.dz",
            "email_ar": "juridique@ecole.dz",
            "adresse": "Siège de l'école – Alger",
            "adresse_ar": "مقر المدرسة – الجزائر"
        }
    },
    "acces": {
        "comment": "Formulaire de demande en ligne + accueil physique.",
        "comment_ar": "استمارة طلب عبر الإنترنت + استقبال حضوري.",
        "mesures": "Vérification d’identité et réponse sous 30 jours.",
        "mesures_ar": "التحقق من الهوية والرد خلال 30 يومًا.",
        "service": {
            "nom": "Service Archives",
            "nom_ar": "مصلحة الأرشيف",
            "mobile": "0551 22 33 44",
            "mobile_ar": "0551 22 33 44",
            "email": "archives@ecole.dz",
            "email_ar": "archives@ecole.dz",
            "adresse": "Bureau des archives – Alger",
            "adresse_ar": "مكتب الأرشيف – الجزائر"
        }
    },
    "rectification": {
        "comment": "Demande via e-mail ou guichet administratif.",
        "comment_ar": "طلب عبر البريد الإلكتروني أو الشباك الإداري.",
        "mesures": "Procédure de correction dans 72 h.",
        "mesures_ar": "إجراء التصحيح خلال 72 ساعة.",
        "service": {
            "nom": "Service Scolarité",
            "nom_ar": "مصلحة التمدرس",
            "mobile": "0552 66 77 88",
            "mobile_ar": "0552 66 77 88",
            "email": "scolarite@ecole.dz",
            "email_ar": "scolarite@ecole.dz",
            "adresse": "Rez-de-chaussée, bâtiment A",
            "adresse_ar": "الطابق الأرضي، المبنى A"
        }
    },
    "opposition": {
        "comment": "Formulaire d’opposition disponible sur le site.",
        "comment_ar": "استمارة اعتراض متاحة على الموقع.",
        "mesures": "Analyse de recevabilité et désactivation des traitements concernés.",
        "mesures_ar": "تحليل قابلية القبول وإيقاف المعالجات المعنية.",
        "service": {
            "nom": "DPO / Protection des données",
            "nom_ar": "مسؤول حماية البيانات",
            "mobile": "0553 99 88 77",
            "mobile_ar": "0553 99 88 77",
            "email": "dpo@ecole.dz",
            "email_ar": "dpo@ecole.dz",
            "adresse": "Direction – 2e étage",
            "adresse_ar": "المديرية – الطابق الثاني"
        }
    }
})




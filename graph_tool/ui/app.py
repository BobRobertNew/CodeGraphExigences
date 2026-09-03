import streamlit as st
import tempfile
import os
import re
import pandas as pd
from graph_tool.infrastructure.networkx_repository import NetworkXGraphRepository
from graph_tool.use_cases.commands import CommandHandler
from graph_tool.use_cases.queries import QueryHandler
import io

# À lancer avec py -m streamlit run app.py

def extract_project_name(filename: str) -> str:
    """Extracts project name from filename format xxx_nomProjet_xxxxx."""
    basename = os.path.splitext(filename)[0]
    parts = basename.split("_")
    if len(parts) >= 3:
        return parts[1]
    elif len(parts) == 2:
        return parts[1]
    return basename

def setup_page():
    st.set_page_config(page_title="Graph Tool UI", layout="wide")
    st.title("Générateur d'Interface Graph Tool")

    st.markdown("""
    Cette interface permet de charger des fichiers pivots (Excel) pour générer des extractions.
    """)

def handle_file_upload():
    st.header("1. Upload de fichiers pivots (Excel)")
    uploaded_files = st.file_uploader(
        "Sélectionnez vos fichiers pivot (.xlsx)",
        type=['xlsx'],
        accept_multiple_files=True
    )
    return uploaded_files

def process_preuves_extraction(uploaded_files):
    if not uploaded_files:
        st.warning("Veuillez d'abord uploader au moins un fichier.")
        return None

    st.info("Création d'un nouveau graphe pour l'extraction...")

    repo = NetworkXGraphRepository()
    cmd = CommandHandler(repo, repo)
    qry = QueryHandler(repo)

    all_results = []

    # Create temp dir if it does not exist (fallback if it was deleted)
    os.makedirs("tmp", exist_ok=True)

    with tempfile.TemporaryDirectory(dir="tmp") as temp_dir:
        for uploaded_file in uploaded_files:
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            project_name = extract_project_name(uploaded_file.name)
            st.write(f"Traitement du projet: **{project_name}** depuis `{uploaded_file.name}`")

            try:
                # Note pour le futur: Pour conserver le graphe entre les différentes actions (ex: bouton 2),
                # on pourrait stocker l'instance `repo` dans st.session_state (ex: st.session_state.repo = repo)
                # et vérifier si elle existe au début de process_preuves_extraction au lieu d'en recréer une.
                cmd.add_project_exigences(
                    project_name=project_name,
                    data_source=file_path,
                    owner="Streamlit User",
                    author="Streamlit User"
                )

                df_preuves = qry.get_preuves_phases_metiers_articles_for_exigences(project_name)
                if not df_preuves.empty:
                    df_preuves.insert(0, 'Projet', project_name)
                    all_results.append(df_preuves)
                else:
                    st.warning(f"Aucune preuve trouvée pour le projet {project_name}.")

            except Exception as e:
                st.error(f"Erreur lors du traitement de {uploaded_file.name}: {e}")

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        return final_df
    return None

def render_actions_and_downloads(uploaded_files):
    st.header("2. Actions")
    st.write("Exécutez des scripts sur les fichiers uploadés.")

    if 'final_df' not in st.session_state:
        st.session_state.final_df = None
    if 'action_name' not in st.session_state:
        st.session_state.action_name = ""

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Extraire la liste des preuves de conformité", type="primary"):
            with st.spinner("Extraction en cours..."):
                st.session_state.final_df = process_preuves_extraction(uploaded_files)
                st.session_state.action_name = "preuves_conformite"

    with col2:
        if st.button("Extraire la liste des exigences (Bientôt disponible)", disabled=True):
            pass

    st.header("3. Résultats et Téléchargements")

    if st.session_state.final_df is not None and not st.session_state.final_df.empty:
        st.success(f"Extraction réussie ! {len(st.session_state.final_df)} lignes générées.")
        st.dataframe(st.session_state.final_df.head())

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.final_df.to_excel(writer, index=False, sheet_name='Preuves')

        excel_data = output.getvalue()

        st.download_button(
            label="📥 Télécharger le fichier Excel",
            data=excel_data,
            file_name=f"extraction_{st.session_state.action_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    elif st.session_state.final_df is not None:
        st.info("L'extraction n'a retourné aucune donnée.")
    else:
        st.write("Aucun résultat à afficher pour le moment. Lancez une action ci-dessus.")

def main():
    setup_page()
    uploaded_files = handle_file_upload()
    render_actions_and_downloads(uploaded_files)

if __name__ == "__main__":
    main()

import re

with open('graph_tool/ui/app.py', 'r') as f:
    content = f.read()

replacement = """
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
"""

content = re.sub(r'try:\s+cmd\.add_project_exigences\(\s+project_name=project_name,\s+data_source=file_path\s+\)', replacement.strip('\n'), content)

with open('graph_tool/ui/app.py', 'w') as f:
    f.write(content)

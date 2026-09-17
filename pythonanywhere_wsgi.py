# ============================================================
# Arquivo WSGI para o PythonAnywhere (plano grátis)
# ------------------------------------------------------------
# COMO USAR:
# 1. Na aba "Web" do PythonAnywhere, abra o link do arquivo WSGI
#    (algo como /var/www/seu_usuario_pythonanywhere_com_wsgi.py)
# 2. APAGUE tudo que está lá e COLE o conteúdo abaixo
# 3. Troque SEU_USUARIO pelo seu username do PythonAnywhere
# 4. Salve e clique em "Reload"
# ============================================================
import sys

USERNAME = "SEU_USUARIO"  # <-- TROQUE AQUI pelo seu username

path = f"/home/{USERNAME}/proweb"
if path not in sys.path:
    sys.path.append(path)

# Opcional (recomendado): chave secreta das sessões.
# import os
# os.environ["SECRET_KEY"] = "troque-por-uma-frase-longa-e-secreta"

from app import app as application

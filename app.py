from flask import Flask, render_template, request, redirect, url_for, session
import json, os, random, uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "quiz-devweb-v2-maratona-140")

BASE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE, "questions.json")
RESULTS_FILE = os.path.join(BASE, "results.json")
UPLOAD_FOLDER = os.path.join(BASE, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED = {"png", "jpg", "jpeg", "gif", "webp"}

def load_questions():
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        return json.load(f)

MODES = {
    "fundamental": "Fundamentos 🌱",
    "avancado": "Avançado 🔥",
    "completo": "Maratona 140 🏁",
}

def scoped_questions():
    """Filtra as questões pelo modo escolhido pelo aluno."""
    qs = load_questions()
    mode = session.get("mode", "fundamental")
    if mode == "avancado":
        return [q for q in qs if q.get("nivel") == "avancado"]
    if mode == "completo":
        return list(qs)
    return [q for q in qs if q.get("nivel") == "fundamental"]

def build_shuffle(questions, seed):
    """Ordem das questões + ordem das alternativas, tudo derivado da seed.

    Determinístico: a mesma seed gera sempre o mesmo embaralhamento,
    então a sessão guarda só 1 número (cabe no cookie até na maratona).
    """
    rng = random.Random(seed)
    order = rng.sample(range(len(questions)), len(questions))
    perms = [rng.sample(range(len(q["opcoes"])), len(q["opcoes"])) for q in questions]
    return order, perms

def effective_questions():
    """Questões do modo do aluno, na ordem sorteada, com alternativas embaralhadas."""
    questions = scoped_questions()
    seed = session.get("seed")
    if seed is None:
        order = list(range(len(questions)))
        perms = [list(range(len(q["opcoes"]))) for q in questions]
    else:
        order, perms = build_shuffle(questions, seed)
    eff = []
    for qi in order:
        q = questions[qi]
        perm = perms[qi] if 0 <= qi < len(perms) else list(range(len(q["opcoes"])))
        eff.append({
            "id": q["id"], "tema": q["tema"], "titulo": q["titulo"],
            "opcoes": [q["opcoes"][i] for i in perm],
            "correta": perm.index(q["correta"]),
            "explicacao": q["explicacao"],
        })
    return eff

def count_hits(questions, answers):
    return sum(1 for i, a in enumerate(answers)
               if i < len(questions) and a == questions[i]["correta"])

def rank_key(r):
    return (-r.get("percentual", 0), -r.get("acertos", 0), r.get("data", ""))

def mode_counts():
    qs = load_questions()
    fund = sum(1 for q in qs if q.get("nivel") == "fundamental")
    avan = sum(1 for q in qs if q.get("nivel") == "avancado")
    return {"fundamental": fund, "avancado": avan, "completo": len(qs)}

def load_results():
    if not os.path.exists(RESULTS_FILE):
        return []
    try:
        with open(RESULTS_FILE, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_results(results):
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

LETTERS = ["A", "B", "C", "D", "E"]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()[:40]
        if not nome:
            return render_template("index.html", erro="Digite seu nome para começar! 🎮",
                                   modes=MODES, counts=mode_counts())
        foto_file = request.files.get("foto")
        foto_url = None
        if foto_file and foto_file.filename:
            ext = foto_file.filename.rsplit(".", 1)[-1].lower() if "." in foto_file.filename else ""
            if ext in ALLOWED:
                fname = f"{uuid.uuid4().hex[:10]}.{ext}"
                foto_file.save(os.path.join(UPLOAD_FOLDER, fname))
                foto_url = f"uploads/{fname}"
        session.clear()
        session["user"] = {"nome": nome, "foto": foto_url}
        modo = request.form.get("modo", "fundamental")
        if modo not in MODES:
            modo = "fundamental"
        session["mode"] = modo
        session["quiz_index"] = 0
        session["answers"] = []
        session["saved"] = False
        session["seed"] = random.randrange(2 ** 31)
        return redirect(url_for("quiz"))
    counts = mode_counts()
    allres = load_results()
    top_modes = []
    for m in ("fundamental", "avancado", "completo"):
        grp = sorted([r for r in allres if r.get("modo") == MODES[m]], key=rank_key)
        top_modes.append((MODES[m], grp[0] if grp else None))
    return render_template("index.html", top_modes=top_modes, modes=MODES, counts=counts)

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "user" not in session:
        return redirect(url_for("index"))
    questions = effective_questions()
    idx = session.get("quiz_index", 0)
    answers = session.get("answers", [])

    if request.method == "POST":
        if idx >= len(questions):
            return redirect(url_for("resultado"))
        try:
            escolha = int(request.form.get("escolha", -1))
        except ValueError:
            escolha = -1
        q = questions[idx]
        answers.append(escolha)
        session["answers"] = answers
        session["quiz_index"] = idx + 1
        session["last"] = {"pos": idx, "escolha": escolha}
        return redirect(url_for("feedback"))

    if idx >= len(questions):
        return redirect(url_for("resultado"))
    q = questions[idx]
    total = len(questions)
    progresso = int(idx / total * 100)
    parciais = count_hits(questions, answers)
    return render_template("quiz.html", q=q, idx=idx, total=total,
                           progresso=progresso, letters=LETTERS,
                           user=session["user"], acertos_parciais=parciais)

@app.route("/feedback")
def feedback():
    if "user" not in session or "last" not in session:
        return redirect(url_for("quiz"))
    marca = session.get("last")
    if not marca:
        return redirect(url_for("quiz"))
    eff = effective_questions()
    pos = marca.get("pos", 0)
    if pos < 0 or pos >= len(eff):
        return redirect(url_for("quiz"))
    q = eff[pos]
    escolha = marca.get("escolha", -1)
    last = {
        "n": pos + 1, "id": q["id"], "tema": q["tema"], "titulo": q["titulo"],
        "opcoes": q["opcoes"], "correta": q["correta"],
        "escolha": escolha, "acertou": (escolha == q["correta"]),
        "explicacao": q["explicacao"],
    }
    idx = session.get("quiz_index", 0)
    total = len(eff)
    ultima = idx >= total
    return render_template("feedback.html", last=last, letters=LETTERS,
                           user=session["user"], idx=idx, total=total,
                           progresso=int(idx / total * 100), ultima=ultima)

@app.route("/resultado")
def resultado():
    if "user" not in session:
        return redirect(url_for("index"))
    questions = effective_questions()
    answers = session.get("answers", [])
    if len(answers) < len(questions):
        return redirect(url_for("quiz"))
    acertos = count_hits(questions, answers)
    total = len(questions)
    percentual = round(acertos / total * 100, 1)

    # monta revisão detalhada
    revisao = []
    for n, (q, a) in enumerate(zip(questions, answers), 1):
        revisao.append({
            "n": n, "id": q["id"], "tema": q["tema"], "titulo": q["titulo"],
            "opcoes": q["opcoes"], "correta": q["correta"],
            "escolha": a, "acertou": (a == q["correta"]),
            "explicacao": q["explicacao"]
        })

    modo_label = MODES.get(session.get("mode", "fundamental"), "")
    # salva no ranking uma única vez
    if not session.get("saved"):
        results = load_results()
        results.append({
            "nome": session["user"]["nome"],
            "foto": session["user"].get("foto"),
            "acertos": acertos,
            "total": total,
            "percentual": percentual,
            "modo": modo_label,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        save_results(results)
        session["saved"] = True

    # mensagem divertida por faixa
    if percentual == 100:
        msg = "LENDÁRIO! 🏆 Você zerou o quiz!"
    elif percentual >= 80:
        msg = "INCRÍVEL! 🚀 Nível sênior!"
    elif percentual >= 60:
        msg = "MUITO BOM! 🎉 Nível pleno!"
    elif percentual >= 40:
        msg = "BOM COMEÇO! 💪 Continue praticando!"
    else:
        msg = "NÃO DESISTA! 🌱 Revise e tente de novo!"

    # posição no ranking DO MODO jogado
    ranking = sorted([r for r in load_results() if r.get("modo") == modo_label], key=rank_key)
    posicao = next((i + 1 for i, r in enumerate(ranking)
                    if r["nome"] == session["user"]["nome"] and r["acertos"] == acertos), "-")

    return render_template("result.html", acertos=acertos, total=total,
                           percentual=percentual, revisao=revisao,
                           letters=LETTERS, user=session["user"],
                           msg=msg, posicao=posicao, modo_label=modo_label)

@app.route("/ranking")
def ranking():
    results = load_results()
    grouped = {}
    for m in ("fundamental", "avancado", "completo"):
        grouped[m] = sorted([r for r in results if r.get("modo") == MODES[m]], key=rank_key)
    sem_modo = sorted([r for r in results if not r.get("modo")], key=rank_key)
    return render_template("ranking.html", grouped=grouped, modes=MODES,
                           mode_order=("fundamental", "avancado", "completo"),
                           sem_modo=sem_modo)

@app.route("/reiniciar")
def reiniciar():
    user = session.get("user")
    mode = session.get("mode", "fundamental")
    session.clear()
    if user:
        session["user"] = user
    session["mode"] = mode
    session["quiz_index"] = 0
    session["answers"] = []
    session["saved"] = False
    session["seed"] = random.randrange(2 ** 31)
    return redirect(url_for("quiz"))

@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    print("\n🎮 Acesse o quiz em: http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)

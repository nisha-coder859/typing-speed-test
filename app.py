from flask import Flask, render_template, request
import time
import pandas as pd
import random
from datetime import datetime
import matplotlib.pyplot as plt

app = Flask(__name__)

def get_paragraph(difficulty):
    filename = f"paragraphs_{difficulty}.txt"  

    with open(filename, "r", encoding="utf-8") as f:
        content = f.read().strip()

    
    paragraphs = content.split("\n\n")

   
    paragraphs = [" ".join(p.split()) for p in paragraphs]

    return random.choice(paragraphs)

def save_result(name, wpm, accuracy, mode):
    entry = {
        "Name":[name],
        "WPM":[round(wpm,2)],
        "Accuracy":[round(accuracy,2)],
        "Mode":[mode],
        "Date":[datetime.now()]
    }
    try:
        df = pd.read_csv("results.csv")
        df = pd.concat([df, pd.DataFrame(entry)], ignore_index=True)
    except:
        df = pd.DataFrame(entry)

    df.to_csv("results.csv", index=False)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/test", methods=["POST"])
def test():
    name = request.form["name"]
    difficulty = request.form["difficulty"]
    time_limit = int(request.form["time"])

    paragraph = get_paragraph(difficulty)

    print("PARAGRAPH SENT TO TEMPLATE:\n", paragraph)  # 👈 ADD THIS

    return render_template(
        "test.html",
        name=name,
        paragraph=paragraph,
        time_limit=time_limit,
        mode="normal"
    )



@app.route("/daily")
def backwards_challenge():
    difficulty = "medium"  
    paragraph = get_paragraph(difficulty)

    return render_template("test.html",
                           name="Daily Challenger",
                           paragraph=paragraph,
                           time_limit=60,
                           mode="backwards",
                           is_daily=True)


@app.route("/result", methods=["POST"])
def result():
    name = request.form["name"]
    typed = request.form["typed"]
    original = request.form["original_para"]
    mode = request.form["mode"]
    time_limit = int(request.form["time_limit"])

    
    start_raw = request.form.get("start")
    if not start_raw:
        start = time.time()
    else:
        start = float(start_raw)

   
    if mode == "backwards":
        typed_compare = typed[::-1]
    else:
        typed_compare = typed

    words_typed = len(typed.split())
    total_words = len(original.split())
    correct = sum(a == b for a, b in zip(
        typed_compare.split(), original.split()
    ))

    accuracy = (correct / total_words) * 100 if total_words else 0
    wpm = (words_typed / time_limit) * 60

    save_result(name, wpm, accuracy, mode.title())

    return render_template(
        "result.html",
        name=name,
        wpm=round(wpm, 2),
        accuracy=round(accuracy, 2)
    )

@app.route("/progress")
def progress():
    df = pd.read_csv("results.csv")

    if df.empty:
        return "No data available"

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["WPM"] = pd.to_numeric(df["WPM"], errors="coerce")
    df["Accuracy"] = pd.to_numeric(df["Accuracy"], errors="coerce")

    df = df.dropna()

    
    df = df[(df["WPM"] > 0) & (df["WPM"] <= 200)]

  
    df["Date"] = df["Date"].dt.strftime("%d %b")

    
    plt.figure(figsize=(14, 6))
    plt.style.use("seaborn-v0_8-darkgrid")

    bars = plt.bar(
        range(len(df)),
        df["WPM"],
        color="#4A90E2",
        edgecolor="#2A6FBD",
        width=0.6,
        label="Typing Speed (WPM)"
    )

    plt.plot(
        range(len(df)),
        df["Accuracy"],
        color="#00CC66",
        marker="o",
        linewidth=2.5,
        markersize=6,
        label="Typing Accuracy (%)"
    )

    plt.xticks(range(len(df)), df["Date"], rotation=30)

    for bar in bars:
        h = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            h + 1,
            f"{int(h)}",
            ha="center",
            fontsize=8
        )

    plt.ylabel("Performance")
    plt.xlabel("Date")
    plt.title("Performance Progress", fontsize=18)
    plt.legend()
    plt.tight_layout()
    plt.savefig("static/progress.png")
    plt.close()

    return render_template("progress.html", img="progress.png")





@app.route("/history")
def history():
    df = pd.read_csv("results.csv")
    return render_template("history.html", data=df.to_dict(orient="records"))


@app.route("/leaderboard")
def leaderboard():
    df = pd.read_csv("results.csv")

    
    df["WPM"] = pd.to_numeric(df["WPM"], errors="coerce")
    df["Accuracy"] = pd.to_numeric(df["Accuracy"], errors="coerce")

    
    df = df.dropna(subset=["WPM", "Accuracy", "Name"])

    
    leaderboard_df = (
        df.groupby("Name", as_index=False)
        .agg(
            Best_WPM=("WPM", "max"),
            Avg_Accuracy=("Accuracy", "mean")
        )
    )

    
    leaderboard_df = leaderboard_df.sort_values(
        by="Best_WPM",
        ascending=False
    ).head(10)

  
    leaderboard_df["Best_WPM"] = leaderboard_df["Best_WPM"].round(1)
    leaderboard_df["Avg_Accuracy"] = leaderboard_df["Avg_Accuracy"].round(1)

    return render_template(
        "leaderboard.html",
        data=leaderboard_df.to_dict(orient="records")
    )



@app.route("/test_again")
def test_again():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001)

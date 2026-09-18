from flask import Flask, render_template, request
import sqlite3
import pickle

app = Flask(__name__)


# --------------------------------------------------
# LOAD AI MODEL
# --------------------------------------------------

with open("milk_model.pkl", "rb") as file:
    model = pickle.load(file)


# --------------------------------------------------
# LOAD BREED ENCODER
# --------------------------------------------------

with open("breed_encoder.pkl", "rb") as file:
    encoder = pickle.load(file)


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def create_database():

    conn = sqlite3.connect("dairy.db")
    cursor = conn.cursor()

    # Animals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS animals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id TEXT,
            age REAL,
            breed TEXT,
            milk REAL,
            feed REAL,
            water REAL
        )
    """)

    # Predictions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id TEXT,
            predicted_milk REAL,
            previous_milk REAL
        )
    """)

    # Check animals table columns
    cursor.execute("PRAGMA table_info(animals)")
    animal_columns = [column[1] for column in cursor.fetchall()]

    if "animal_id" not in animal_columns:
        cursor.execute(
            "ALTER TABLE animals ADD COLUMN animal_id TEXT"
        )

    if "age" not in animal_columns:
        cursor.execute(
            "ALTER TABLE animals ADD COLUMN age REAL"
        )

    if "breed" not in animal_columns:
        cursor.execute(
            "ALTER TABLE animals ADD COLUMN breed TEXT"
        )

    if "milk" not in animal_columns:
        cursor.execute(
            "ALTER TABLE animals ADD COLUMN milk REAL"
        )

    if "feed" not in animal_columns:
        cursor.execute(
            "ALTER TABLE animals ADD COLUMN feed REAL"
        )

    if "water" not in animal_columns:
        cursor.execute(
            "ALTER TABLE animals ADD COLUMN water REAL"
        )

    # Check predictions table columns
    cursor.execute("PRAGMA table_info(predictions)")
    prediction_columns = [column[1] for column in cursor.fetchall()]

    if "animal_id" not in prediction_columns:
        cursor.execute(
            "ALTER TABLE predictions ADD COLUMN animal_id TEXT"
        )

    if "predicted_milk" not in prediction_columns:
        cursor.execute(
            "ALTER TABLE predictions ADD COLUMN predicted_milk REAL"
        )

    if "previous_milk" not in prediction_columns:
        cursor.execute(
            "ALTER TABLE predictions ADD COLUMN previous_milk REAL"
        )

    conn.commit()
    conn.close()


# --------------------------------------------------
# FARM HEALTH SCORE
# --------------------------------------------------

def calculate_health_score(milk, feed, water):

    score = 0

    # Milk score
    if milk >= 15:
        score += 40
    elif milk >= 10:
        score += 30
    elif milk >= 7:
        score += 20
    else:
        score += 10

    # Feed score
    if feed >= 10:
        score += 30
    elif feed >= 8:
        score += 25
    elif feed >= 6:
        score += 15
    else:
        score += 10

    # Water score
    if water >= 35:
        score += 30
    elif water >= 25:
        score += 25
    elif water >= 20:
        score += 15
    else:
        score += 10

    # Health status
    if score >= 80:
        status = "Excellent Farm Condition"
    elif score >= 60:
        status = "Good Farm Condition"
    elif score >= 40:
        status = "Needs Attention"
    else:
        status = "Needs Improvement"

    return score, status


# --------------------------------------------------
# HOME / DASHBOARD
# --------------------------------------------------

@app.route("/")
def home():

    conn = sqlite3.connect("dairy.db")
    cursor = conn.cursor()

    # Total animals
    cursor.execute("""
        SELECT COUNT(*) FROM animals
    """)

    total_animals = cursor.fetchone()[0]

    # Average milk
    cursor.execute("""
        SELECT AVG(milk) FROM animals
    """)

    avg_milk_result = cursor.fetchone()[0]

    if avg_milk_result is None:
        avg_milk = 0
    else:
        avg_milk = round(avg_milk_result, 2)

    # Animal records
    cursor.execute("""
        SELECT animal_id, age, breed, milk, feed, water
        FROM animals
        ORDER BY id DESC
    """)

    animal_data = cursor.fetchall()

    # Chart data
    cursor.execute("""
        SELECT animal_id, milk
        FROM animals
        ORDER BY id
    """)

    chart_data = cursor.fetchall()

    animal_ids = [row[0] for row in chart_data]
    milk_values = [row[1] for row in chart_data]

    # Prediction history
    cursor.execute("""
        SELECT animal_id, predicted_milk, previous_milk
        FROM predictions
        ORDER BY id DESC
        LIMIT 5
    """)

    prediction_history = cursor.fetchall()

    # Latest prediction
    latest_prediction = None
    prediction_change = None
    prediction_status = ""

    if prediction_history:

        latest_prediction = prediction_history[0]

        animal_id = latest_prediction[0]
        predicted_milk = latest_prediction[1]
        previous_milk = latest_prediction[2]

        if previous_milk is not None:

            prediction_change = round(
                predicted_milk - previous_milk,
                2
            )

            if prediction_change > 0:
                prediction_status = "📈 Expected Increase"

            elif prediction_change < 0:
                prediction_status = "📉 Expected Decrease"

            else:
                prediction_status = "➡️ Expected Stable Production"

    # --------------------------------------------------
    # SMART ALERTS
    # --------------------------------------------------

    alerts = []
    recommendations = []

    for animal in animal_data:

        animal_id = animal[0]
        milk = animal[3]
        feed = animal[4]
        water = animal[5]

        if milk < 10:

            alerts.append(
                f"Animal {animal_id}: Milk production is low."
            )

            recommendations.append(
                f"Animal {animal_id}: Monitor feed quality and daily milk production."
            )

        if water < 25:

            alerts.append(
                f"Animal {animal_id}: Water intake is low."
            )

            recommendations.append(
                f"Animal {animal_id}: Ensure sufficient clean drinking water."
            )

        if feed < 7:

            alerts.append(
                f"Animal {animal_id}: Feed quantity is low."
            )

            recommendations.append(
                f"Animal {animal_id}: Review the daily feed quantity."
            )

    # Default messages
    if not alerts:

        alerts.append(
            "No major alerts detected from the available farm data."
        )

    if not recommendations:

        recommendations.append(
            "Farm data looks good. Continue regular monitoring."
        )

    # --------------------------------------------------
    # AUTOMATIC FARM HEALTH SCORE
    # --------------------------------------------------

    if animal_data:

        total_score = 0

        for animal in animal_data:

            milk = animal[3]
            feed = animal[4]
            water = animal[5]

            score, status = calculate_health_score(
                milk,
                feed,
                water
            )

            total_score += score

        health_score = round(
            total_score / len(animal_data)
        )

        if health_score >= 80:
            health_status = "Excellent Farm Condition"

        elif health_score >= 60:
            health_status = "Good Farm Condition"

        elif health_score >= 40:
            health_status = "Needs Attention"

        else:
            health_status = "Needs Improvement"

    else:

        health_score = 0
        health_status = "No Farm Data Yet"

    conn.close()

    return render_template(
        "index.html",
        total_animals=total_animals,
        avg_milk=avg_milk,
        animal_data=animal_data,
        animal_ids=animal_ids,
        milk_values=milk_values,
        alerts=alerts,
        recommendations=recommendations,
        prediction_history=prediction_history,
        latest_prediction=latest_prediction,
        prediction_change=prediction_change,
        prediction_status=prediction_status,
        health_score=health_score,
        health_status=health_status
    )


# --------------------------------------------------
# SAVE ANIMAL
# --------------------------------------------------

@app.route("/save_animal", methods=["POST"])
def save_animal():

    animal_id = request.form.get("animal_id")
    age = float(request.form.get("age"))
    breed = request.form.get("breed")
    milk = float(request.form.get("milk"))
    feed = float(request.form.get("feed"))
    water = float(request.form.get("water"))

    conn = sqlite3.connect("dairy.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO animals
        (animal_id, age, breed, milk, feed, water)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        animal_id,
        age,
        breed,
        milk,
        feed,
        water
    ))

    conn.commit()
    conn.close()

    return """
        <h2>✅ Animal data saved successfully!</h2>
        <p><a href="/">Go back to Dashboard</a></p>
    """


# --------------------------------------------------
# AI MILK PREDICTION
# --------------------------------------------------

@app.route("/predict", methods=["POST"])
def predict():

    animal_id = request.form.get("animal_id")

    age = float(request.form.get("age"))

    breed = request.form.get("breed")

    feed = float(request.form.get("feed"))

    water = float(request.form.get("water"))

    # Get previous milk
    milk_value = request.form.get("milk")

    if milk_value:

        previous_milk = float(milk_value)

    else:

        conn = sqlite3.connect("dairy.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT milk
            FROM animals
            WHERE animal_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (animal_id,))

        result = cursor.fetchone()

        conn.close()

        if result:
            previous_milk = float(result[0])
        else:
            previous_milk = 0.0

    # Check breed
    if breed not in encoder.classes_:

        return """
            <h2>❌ Invalid breed selected.</h2>
            <p><a href="/">Go back</a></p>
        """

    # Encode breed
    breed_encoded = encoder.transform([breed])[0]

    # Prepare input
    input_data = [[
        age,
        breed_encoded,
        previous_milk,
        feed,
        water
    ]]

    # AI prediction
    predicted_milk = model.predict(input_data)[0]

    predicted_milk = round(
        float(predicted_milk),
        2
    )

    # Calculate change
    prediction_change = round(
        predicted_milk - previous_milk,
        2
    )

    # Status
    if prediction_change > 0:

        prediction_status = "📈 Expected Increase"

    elif prediction_change < 0:

        prediction_status = "📉 Expected Decrease"

    else:

        prediction_status = "➡️ Expected Stable Production"

    # Save prediction
    conn = sqlite3.connect("dairy.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO predictions
        (animal_id, predicted_milk, previous_milk)
        VALUES (?, ?, ?)
    """, (
        animal_id,
        predicted_milk,
        previous_milk
    ))

    conn.commit()
    conn.close()

    return f"""
        <html>

        <head>

            <title>AI Prediction Result</title>

            <style>

                body {{
                    font-family: Arial;
                    background: #f4f8f4;
                    text-align: center;
                    padding: 50px;
                }}

                .box {{
                    background: white;
                    max-width: 500px;
                    margin: auto;
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 3px 12px rgba(0,0,0,0.1);
                }}

                h1 {{
                    color: #2e7d32;
                }}

                .value {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #1565c0;
                }}

                .status {{
                    font-size: 20px;
                    margin-top: 15px;
                }}

                a {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 20px;
                    background: #2e7d32;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                }}

            </style>

        </head>

        <body>

            <div class="box">

                <h1>
                    🤖 AI Prediction Result
                </h1>

                <p>
                    Animal ID:
                    <b>{animal_id}</b>
                </p>

                <p>
                    Previous Milk
                </p>

                <div class="value">
                    {previous_milk} L
                </div>

                <p>
                    AI Predicted Milk
                </p>

                <div class="value">
                    {predicted_milk} L
                </div>

                <p>
                    Production Change
                </p>

                <div class="value">
                    {prediction_change} L
                </div>

                <div class="status">
                    {prediction_status}
                </div>

                <a href="/">
                    ← Back to Dashboard
                </a>

            </div>

        </body>

        </html>
    """


# --------------------------------------------------
# WHAT-IF SIMULATOR
# --------------------------------------------------

@app.route("/simulate", methods=["POST"])
def simulate():

    animal_id = request.form.get("animal_id")

    age = float(request.form.get("age"))

    breed = request.form.get("breed")

    previous_milk = float(
        request.form.get("milk")
    )

    current_feed = float(
        request.form.get("current_feed")
    )

    current_water = float(
        request.form.get("current_water")
    )

    simulated_feed = float(
        request.form.get("simulated_feed")
    )

    simulated_water = float(
        request.form.get("simulated_water")
    )

    # Check breed
    if breed not in encoder.classes_:

        return """
            <h2>❌ Invalid breed selected.</h2>
            <p><a href="/">Go back</a></p>
        """

    # Encode breed
    breed_encoded = encoder.transform([breed])[0]

    # --------------------------------------------------
    # CURRENT SITUATION
    # --------------------------------------------------

    current_input = [[
        age,
        breed_encoded,
        previous_milk,
        current_feed,
        current_water
    ]]

    current_prediction = model.predict(
        current_input
    )[0]

    current_prediction = round(
        float(current_prediction),
        2
    )

    # --------------------------------------------------
    # SIMULATED SITUATION
    # --------------------------------------------------

    simulated_input = [[
        age,
        breed_encoded,
        previous_milk,
        simulated_feed,
        simulated_water
    ]]

    simulated_prediction = model.predict(
        simulated_input
    )[0]

    simulated_prediction = round(
        float(simulated_prediction),
        2
    )

    # --------------------------------------------------
    # SIMULATION CHANGE
    # --------------------------------------------------

    simulation_change = round(
        simulated_prediction - current_prediction,
        2
    )

    # Status
    if simulation_change > 0:

        simulation_status = "📈 Production may increase"

    elif simulation_change < 0:

        simulation_status = "📉 Production may decrease"

    else:

        simulation_status = "➡️ Production may remain stable"

    return f"""
        <html>

        <head>

            <title>What-If Simulator</title>

            <style>

                body {{
                    font-family: Arial;
                    background: #f4f8f4;
                    text-align: center;
                    padding: 40px;
                }}

                .box {{
                    background: white;
                    max-width: 700px;
                    margin: auto;
                    padding: 30px;
                    border-radius: 18px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.12);
                }}

                h1 {{
                    color: #2e7d32;
                }}

                .cards {{
                    display: flex;
                    gap: 20px;
                    justify-content: center;
                    margin-top: 25px;
                    flex-wrap: wrap;
                }}

                .card {{
                    background: #f1f8e9;
                    padding: 20px;
                    border-radius: 12px;
                    min-width: 240px;
                }}

                .value {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #1565c0;
                }}

                .change {{
                    font-size: 25px;
                    font-weight: bold;
                    margin-top: 30px;
                }}

                .status {{
                    font-size: 20px;
                    margin-top: 15px;
                }}

                .note {{
                    margin-top: 25px;
                    color: #555;
                    font-size: 14px;
                }}

                a {{
                    display: inline-block;
                    margin-top: 25px;
                    padding: 12px 22px;
                    background: #2e7d32;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                }}

            </style>

        </head>

        <body>

            <div class="box">

                <h1>
                    🔮 What-If Simulator
                </h1>

                <p>
                    Animal ID:
                    <b>{animal_id}</b>
                </p>

                <div class="cards">

                    <div class="card">

                        <h3>
                            📊 Current Situation
                        </h3>

                        <p>Feed</p>

                        <div class="value">
                            {current_feed} kg
                        </div>

                        <p>Water</p>

                        <div class="value">
                            {current_water} L
                        </div>

                        <p>Predicted Milk</p>

                        <div class="value">
                            {current_prediction} L
                        </div>

                    </div>


                    <div class="card">

                        <h3>
                            🔮 What-If Situation
                        </h3>

                        <p>Feed</p>

                        <div class="value">
                            {simulated_feed} kg
                        </div>

                        <p>Water</p>

                        <div class="value">
                            {simulated_water} L
                        </div>

                        <p>Predicted Milk</p>

                        <div class="value">
                            {simulated_prediction} L
                        </div>

                    </div>

                </div>


                <div class="change">

                    Expected Change:
                    {simulation_change} L

                </div>


                <div class="status">

                    {simulation_status}

                </div>


                <div class="note">

                    💡 This is an AI-based estimate for
                    decision support. It is not a guaranteed
                    production result.

                </div>


                <a href="/">
                    ← Back to Dashboard
                </a>

            </div>

        </body>

        </html>
    """


# --------------------------------------------------
# RUN APP
# --------------------------------------------------

if __name__ == "__main__":

    create_database()

    app.run(debug=True)
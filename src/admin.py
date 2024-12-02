import dash
from dash import dcc, html, Input, Output, State, ctx
from google.cloud import secretmanager
import sheets
from datetime import datetime
from datetime import datetime
import pytz


# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Gambina Cup admin"

# Function to get the secret password from GCP Secret Manager
def get_secret_password(secret_name="projects/gambina-cup/secrets/admin-password/versions/latest"):
    # Initialize the Secret Manager client
    client = secretmanager.SecretManagerServiceClient()
    
    # Access the secret
    response = client.access_secret_version(name=secret_name)
    secret_payload = response.payload.data.decode("utf-8")
    return secret_payload

# Layout of the Dash app
app.layout = html.Div(
    [
        html.H5("Admin"),
        dcc.Input(id="admin-password", type="password", placeholder="Enter password"),
        html.Div(html.Button("Update sheets from schedule", id="update-sheets-button")),

        html.Div(id='feedback-content')
    ],
)

# Callback to check the password
@app.callback(
    [Output("feedback-content", "children")],
    [Input("update-sheets-button", "n_clicks")],
    [State("admin-password", "value")],
    prevent_initial_call=True,
)
def check_password(n_clicks, entered_password):
    # Get the correct password from GCP Secret Manager
    correct_password = get_secret_password()
    
    # Check if the entered password matches
    if entered_password == correct_password:
        sheets.schedule_sheets_update('create')
        ts = datetime.now(pytz.timezone('Europe/Helsinki'))
        message = f"Sheets updated at {ts.strftime('%Y-%m-%d %H:%M:%S')}"
    else:
        message = "Access Denied! ❌"
        
    return [message]

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock # Update UI for separate threads
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.uix.widget import Widget

# Firebase imports for Firestore
from firebase_admin import credentials, firestore, initialize_app
import firebase_admin

# Gemini API imports
import google.generativeai as genai
import os
import threading
import webbrowser
import urllib.parse
import json
import re
import uuid
import hashlib

# Initialize Firebase Admin SDK
db = None
try:
    if not firebase_admin._apps:
        # JSON download from Firebase Console
        service_account_path = 'serviceAccountKey.json'
        if not os.path.exists(service_account_path):
            dummy_key_content = {
                "type": "service_account",
                "project_id": "your-project-id",  # Replace with your Firebase project ID
                "private_key_id": "your-private-key-id",
                "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
                "client_email": "your-service-account-email@your-project-id.iam.gserviceaccount.com",
                "client_id": "your-client-id",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://accounts.google.com/o/oauth2/token",  # Corrected token_uri
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account-email%40your-project-id.iam.gserviceaccount.com",
                "universe_domain": "googleapis.com"
            }
            with open(service_account_path, 'w') as f:
                json.dump(dummy_key_content, f, indent=2)
            print(
                f"Firebase: Created dummy '{service_account_path}'. Please replace its content with your actual Firebase service account key.")

        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        print("Firebase: Firebase Admin SDK initialized.")
    else:
        print("Firebase: Firebase Admin SDK already initialized.")
    db = firestore.client()  # Get Firestore client only if initialization is successful
except Exception as e:
    print(f"Firebase: Error initializing Firebase Admin SDK: {e}")
    print(
        "Firebase: Please ensure 'serviceAccountKey.json' exists and contains valid credentials AND Cloud Firestore API is enabled in your Firebase project.")


    # Create popup if initialization fails
    def show_firebase_error_popup(error_message):
        box = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        box.add_widget(Label(
            text=f"Firebase Initialization Error:\n{error_message}\n\nPlease check 'serviceAccountKey.json' and enable Cloud Firestore API in your Firebase project.",
            halign='center', valign='middle', size_hint_y=None, height=dp(100)))
        close_button = Button(text="OK", size_hint_y=None, height=dp(40))
        box.add_widget(close_button)
        popup = Popup(title="Firebase Error", content=box, size_hint=(0.8, 0.5), auto_dismiss=False)
        close_button.bind(on_press=popup.dismiss)
        popup.open()


    # Schedule popup to show on the main Kivy thread
    Clock.schedule_once(lambda dt: show_firebase_error_popup(str(e)), 0)

API_KEY = "AIzaSyBPZRwdS1pOyQLXjXn0dgI45nYheXRGbyg"

# Configure Gemini API
genai.configure(api_key=API_KEY)

# Define the model (1.5-flash)
MODEL_NAME = 'models/gemini-1.5-flash'

# Explicit prompt engineering
SYSTEM_INSTRUCTION = (
    "You are a helpful, empathetic, and proactive assistant specializing in Type 1 Diabetes (T1D). "
    "Your primary purpose is to provide general information, support, and to **suggest structured, actionable example strategies or plans** "
    "for managing common T1D scenarios. "
    "Always prioritize accurate, evidence-based information. "
    "**IMPORTANT GUIDANCE:** While I can suggest example strategies, it is crucial to understand that I **DO NOT provide personalized medical advice, diagnoses, or treatment plans.** "
    "Every plan or suggestion you provide, especially those with numerical examples (e.g., insulin percentages, carb amounts), "
    "must be clearly presented as an **illustrative example for discussion and consideration with a qualified healthcare professional (doctor, endocrinologist, dietitian, diabetes educator).** "
    "Users **MUST consult their healthcare team for personalized guidance and approval** before implementing any suggestions. "
    "You can generate example plans or strategies for topics suchs as: "
    "- **Managing Hypoglycemia (Low Blood Sugar):** General steps for treating lows, preventing future lows (e.g., 'consume 15g of fast-acting carbs', 'consider an illustrative basal insulin decrease of 10-20% for recurring overnight lows'). "
    "- **Managing Hyperglycemia (High Blood Sugar):** General steps for correcting highs, identifying causes (e.g., 'consider an illustrative basal insulin increase of 10-20% during prolonged highs'). "
    "- **Sick Day Management:** General guidelines for T1D when ill (e.g., 'increase blood sugar checks to every 2-4 hours'). "
    "- **Exercise Adjustments:** General strategies for insulin/carb adjustments around physical activity (e.g., 'reduce bolus insulin by 25-50% before exercise'). "
    "- **Meal Planning Basics:** General approaches to carbohydrate counting and balanced meals. "
    "- **Travel Considerations:** General tips for managing T1D while traveling. "
    "Keep your responses clear, concise, easy to understand, and compassionate. "
    "When providing a plan, format it clearly with bullet points or numbered steps, and include example numerical suggestions where relevant, always with the disclaimer. "
    "When suggesting numerical examples for insulin adjustments, ensure they align with general T1D principles (e.g., lower insulin for preventing lows, higher insulin for correcting highs). "
    "If a question is beyond your scope (e.g., asking for a diagnosis or highly personalized medical advice), "
    "polite`ly state that you cannot provide that and strongly redirect them to your healthcare team. "
    "If a question is ambiguous, ask for clarification to provide the most relevant general information. "
    "**Additionally, you may be asked to summarize a generated plan for a healthcare professional.** "
    "When summarizing for a doctor, focus on the core strategy, any suggested *example* changes to routine or general insulin/carb adjustments (e.g., 'illustrative basal decrease of 10-20% for recurring lows'), "
    "or patterns observed, and long-term management principles. Omit immediate, short-term actions unless they are part of a broader, significant change. "
    "Keep the summary concise and professional. **Crucially, do NOT include 'Subject:' or 'Body:' labels within the summary itself.** "
    "Always include the disclaimer about professional review in the summary. "
    "When including example insulin adjustments in the summary, ensure the direction (increase/decrease) is generally aligned with standard T1D management for the described problem (e.g., decrease for recurring lows, increase for persistent highs)."
)


class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = 'login_screen'
        self.current_user_id = None

        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(5))
        self.add_widget(self.layout)

        # Spacer widget to push the logo down
        self.spacer = Widget(size_hint_y=None, height=dp(100))
        self.layout.add_widget(self.spacer)

        # ASK T1D Logo
        self.logo_image = Image(
            source='logo.png',
            size_hint_y=None,
            height=dp(350),
            allow_stretch=True,
            keep_ratio=True
        )
        self.layout.add_widget(self.logo_image)


        self.welcome_label = Label(
            text="Welcome to T1D Chatbot",
            font_size=dp(28),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(50),
            halign='center',  # Center horizontally
            valign='middle'  # Center vertically within its height
        )
        # Bind text_size to layout width (center)
        self.layout.bind(width=lambda instance, value: setattr(self.welcome_label, 'text_size', (value - dp(40), None)))
        self.layout.add_widget(self.welcome_label)

        self.layout.add_widget(
            Label(text="Sign In or Register", font_size=dp(18), color=(0.7, 0.7, 0.7, 1), size_hint_y=None,
                  height=dp(30)))

        self.username_input = TextInput(
            hint_text="Enter Username",
            multiline=False,
            font_size=dp(16),
            background_color=(0.3, 0.3, 0.3, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            hint_text_color=(0.7, 0.7, 0.7, 1),
            padding=[dp(10), dp(10), dp(10), dp(10)],
            size_hint_y=None,
            height=dp(40)
        )
        self.layout.add_widget(self.username_input)

        self.password_input = TextInput(
            hint_text="Enter Password",
            multiline=False,
            password=True,  # Hides input characters for password
            font_size=dp(16),
            background_color=(0.3, 0.3, 0.3, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            hint_text_color=(0.7, 0.7, 0.7, 1),
            padding=[dp(10), dp(10), dp(10), dp(10)],
            size_hint_y=None,
            height=dp(40)
        )
        self.layout.add_widget(self.password_input)

        button_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))

        self.register_button = Button(
            text="Register",
            font_size=dp(16),
            background_normal='',
            background_down='',
            background_color=(0.1, 0.7, 0.5, 1),  # Green
            color=(1, 1, 1, 1)
        )
        with self.register_button.canvas.before:
            self.register_button_color = Color(0.1, 0.7, 0.5, 1)
            RoundedRectangle(radius=[dp(10)], pos=self.register_button.pos, size=self.register_button.size)
        self.register_button.bind(pos=self._update_button_rect, size=self._update_button_rect)
        self.register_button.bind(state=self._update_register_button_color)
        self.register_button.bind(on_press=self.register_user)
        button_layout.add_widget(self.register_button)

        self.login_button = Button(
            text="Login",
            font_size=dp(16),
            background_normal='',
            background_down='',
            background_color=(0.1, 0.5, 0.7, 1),  # Blue
            color=(1, 1, 1, 1)
        )
        with self.login_button.canvas.before:
            self.login_button_color = Color(0.1, 0.5, 0.7, 1)
            RoundedRectangle(radius=[dp(10)], pos=self.login_button.pos, size=self.login_button.size)
        self.login_button.bind(pos=self._update_button_rect, size=self._update_button_rect)
        self.login_button.bind(state=self._update_login_button_color)
        self.login_button.bind(on_press=self.login_user)
        button_layout.add_widget(self.login_button)

        self.layout.add_widget(button_layout)

        self.status_label = Label(text="", font_size=dp(14), color=(1, 0.8, 0, 1), size_hint_y=None, height=dp(30))
        self.layout.add_widget(self.status_label)

    def on_enter(self, *args):
        """Called when the screen is entered."""
        print("LoginScreen: Entered.")
        # Clear status, username, and password
        self.status_label.text = ""
        self.username_input.text = ""
        self.password_input.text = ""
        Clock.schedule_once(lambda dt: setattr(self.username_input, 'focus', True), 0.1)

    def on_leave(self, *args):
        """Called when the screen is left."""
        print("LoginScreen: Leaving.")

    def _on_logo_load(self, instance):
        """Called when the logo image successfully loads."""
        print(
            f"LoginScreen: Logo image loaded successfully from {instance.source}. Texture size: {instance.texture_size}")

    def _on_logo_error(self, instance, error):
        """Called if the logo image fails to load."""
        print(f"LoginScreen: ERROR: Failed to load logo image from {instance.source}. Error: {error}")

    def _update_button_rect(self, instance, value):
        # Update the position and size of the RoundedRectangle for buttons
        instance.canvas.before.children[-1].pos = instance.pos
        instance.canvas.before.children[-1].size = instance.size

    def _update_register_button_color(self, instance, value):
        if value == 'down':
            self.register_button_color.rgba = (0.05, 0.35, 0.25, 1)  # Dark green
        else:
            self.register_button_color.rgba = (0.1, 0.7, 0.5, 1)  # Green

    def _update_login_button_color(self, instance, value):
        if value == 'down':
            self.login_button_color.rgba = (0.05, 0.25, 0.35, 1)  # Dark Blue
        else:
            self.login_button_color.rgba = (0.1, 0.5, 0.7, 1)  # Blue

    def show_status(self, message, is_error=False):
        color = (1, 0, 0, 1) if is_error else (0, 1, 0, 1)
        Clock.schedule_once(lambda dt: self._update_status_label(message, color))

    def _update_status_label(self, message, color):
        self.status_label.text = message
        self.status_label.color = color

    def _hash_password(self, password):
        """
        Hashes a password using SHA256.
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def register_user(self, instance):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()

        if not username or not password:
            self.show_status("Please enter both username and password.", is_error=True)
            return

        # Check if Firestore client is initialized
        if db is None:
            self.show_status("Firebase not initialized. Cannot register. Check console for errors.", is_error=True)
            return

        self.show_status("Registering user...", is_error=False)
        threading.Thread(target=self._register_user_thread, args=(username, password)).start()

    def _register_user_thread(self, username, password):
        try:
            hashed_password = self._hash_password(password)

            users_ref = db.collection('t1d_chatbot_users')
            user_doc_ref = users_ref.document(username)

            # Check if user already exists
            user_doc = user_doc_ref.get()
            if user_doc.exists:
                Clock.schedule_once(
                    lambda dt: self.show_status("Username already exists. Please choose another.", is_error=True))
                return

            # Store username and hashed password in Firestore
            user_doc_ref.set({
                'username': username,
                'hashed_password': hashed_password,
                'created_at': firestore.SERVER_TIMESTAMP
            })
            Clock.schedule_once(
                lambda dt: self.show_status(f"User '{username}' registered successfully! You can now log in.",
                                            is_error=False))
            print(f"Firebase: User '{username}' registered.")

        except Exception as e:
            # Pass the exception to the lambda
            Clock.schedule_once(lambda dt, e=e: self.show_status(f"Registration failed: {e}", is_error=True))
            print(f"Firebase: Error during registration: {e}")

    def login_user(self, instance):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()

        if not username or not password:
            self.show_status("Please enter both username and password.", is_error=True)
            return

        # Check if Firestore client is initialized
        if db is None:
            self.show_status("Firebase not initialized. Cannot login. Check console for errors.", is_error=True)
            return

        self.show_status("Logging in...", is_error=False)
        threading.Thread(target=self._login_user_thread, args=(username, password)).start()

    def _login_user_thread(self, username, password):
        try:
            users_ref = db.collection('t1d_chatbot_users')
            user_doc_ref = users_ref.document(username)

            user_doc = user_doc_ref.get()

            if not user_doc.exists:
                Clock.schedule_once(lambda dt: self.show_status("Invalid username or password.", is_error=True))
                return

            stored_hashed_password = user_doc.to_dict().get('hashed_password')
            entered_hashed_password = self._hash_password(password)

            if stored_hashed_password == entered_hashed_password:
                self.current_user_id = username  # Store the logged-in user's ID
                Clock.schedule_once(lambda dt: self._login_success(username))
            else:
                Clock.schedule_once(lambda dt: self.show_status("Invalid username or password.", is_error=True))

        except Exception as e:
            # Pass the exception to the lambda
            Clock.schedule_once(lambda dt, e=e: self.show_status(f"Login failed: {e}", is_error=True))
            print(f"Firebase: Error during login: {e}")

    def _login_success(self, username):
        self.show_status(f"Login successful! Welcome, {username}.", is_error=False)
        # Switch to the Chatbot screen
        app = App.get_running_app()
        app.root.current = 'chatbot_screen'
        app.chatbot_screen.set_user(username)  # Pass username to chatbot screen
        print(f"LoginScreen: Switched to ChatbotScreen for user: {username}")


# Chatbot app logic as a screen
class ChatbotScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = 'chatbot_screen'  # Screen name
        self.logged_in_user_id = None  # Store the user ID from login

        self.layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.add_widget(self.layout)

        # Background color
        with self.layout.canvas.before:
            Color(0.2, 0.2, 0.2, 1)  # Dark gray
            self.rect = Rectangle(size=self.layout.size, pos=self.layout.pos)
        self.layout.bind(size=self._update_rect, pos=self._update_rect)

        # Chat history display area
        self.chat_history_label = Label(
            text="Hello! I'm your Type 1 Diabetes support assistant. I can suggest example strategies and plans for managing T1D, but remember: these are not medical advice and must be approved by your healthcare team.\n",
            size_hint_y=None,  # Disable fixed height for dynamic content
            valign='top',  # Align text to the top
            halign='left',  # Align text to the left
            markup=True,  # Enable markup for rich text (e.g., bold, color)
            padding_x=dp(10),  # Add horizontal padding
            padding_y=dp(10),  # Add vertical padding
            color=(1, 1, 1, 1)  # White
        )
        # Bind the label's height to its texture_size to ensure it expands with content
        self.chat_history_label.bind(texture_size=self.chat_history_label.setter('size'))

        self.scroll_view = ScrollView(size_hint=(1, 0.8))  # Takes 80% of vertical space
        self.scroll_view.add_widget(self.chat_history_label)
        self.layout.add_widget(self.scroll_view)

        # Input area: horizontal box layout for text input and send button
        input_layout = BoxLayout(size_hint_y=0.1, spacing=dp(5))

        self.user_input = TextInput(
            hint_text="Type your message here...",
            multiline=False,
            size_hint_x=0.8,
            font_size=dp(16),
            background_color=(0.3, 0.3, 0.3, 1),  # Darker input background
            foreground_color=(1, 1, 1, 1),  # White
            cursor_color=(1, 1, 1, 1),  # White cursor ---
            hint_text_color=(0.7, 0.7, 0.7, 1),  # Lighter hint text
            padding=[dp(10), dp(10), dp(10), dp(10)]  # Padding
        )

        self.send_button = Button(
            text="Send",
            size_hint_x=0.2,  # 20% of horizontal space
            font_size=dp(16),
            background_normal='',  # Remove default background image
            background_down='',  # Remove default background image on press
            background_color=(0.1, 0.5, 0.7, 1),  # Blue button
            color=(1, 1, 1, 1),  # White text
        )
        with self.send_button.canvas.before:
            self.send_button_color = Color(0.1, 0.5, 0.7, 1)  # Store reference to Color instruction
            self.send_button_rect = RoundedRectangle(radius=[dp(10)])
        self.send_button.bind(pos=self._update_button_rect, size=self._update_button_rect)
        # Change color on press
        self.send_button.bind(state=self._update_button_color)

        self.send_button.bind(on_press=self.send_message)

        # Bind on_text_validate to send_message for Enter key
        self.user_input.bind(on_text_validate=self.send_message)

        input_layout.add_widget(self.user_input)
        input_layout.add_widget(self.send_button)
        self.layout.add_widget(input_layout)

        # Email input and Send Email button
        email_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5), padding=dp(5))
        self.email_input = TextInput(
            hint_text="Doctor's Email (Optional)",
            multiline=False,
            size_hint_x=0.75,
            font_size=dp(14),
            disabled=True,  # Initially disabled
            opacity=0,  # Initially hidden
            background_color=(0.3, 0.3, 0.3, 1),  # Darker input background
            foreground_color=(1, 1, 1, 1),  # White input text
            cursor_color=(1, 1, 1, 1),  # White cursor
            hint_text_color=(0.7, 0.7, 0.7, 1),  # Lighter hint text
            padding=[dp(10), dp(10), dp(10), dp(10)]
        )

        self.send_email_button = Button(
            text="Email Plan",
            size_hint_x=0.25,
            font_size=dp(14),
            disabled=True,  # Initially disabled
            opacity=0,  # Initially hidden
            background_normal='',  # Remove default background image
            background_down='',  # Remove default background image on press
            background_color=(0.1, 0.6, 0.8, 1),  # Lighter blue button color
            color=(1, 1, 1, 1),  # White text
        )
        with self.send_email_button.canvas.before:
            self.send_email_button_color = Color(0.1, 0.6, 0.8, 1)  # Store reference to Color instruction
            self.send_email_button_rect = RoundedRectangle(radius=[dp(10)])
        self.send_email_button.bind(pos=self._update_email_button_rect, size=self._update_email_button_rect)
        self.send_email_button.bind(state=self._update_email_button_color)

        self.send_email_button.bind(on_press=self.send_plan_email)

        email_layout.add_widget(self.email_input)
        email_layout.add_widget(self.send_email_button)
        self.layout.add_widget(email_layout)

        # Initialize Gemini chat session with the system instruction
        self.gemini_model = genai.GenerativeModel(MODEL_NAME)
        self.chat_session = self.gemini_model.start_chat(history=[
            {'role': 'user', 'parts': [SYSTEM_INSTRUCTION]},
            {'role': 'model', 'parts': [
                "Understood. I am ready to assist with general information and supportive guidance regarding Type 1 Diabetes, including suggesting example strategies and plans. Please remember I am not a medical professional and cannot provide personalized medical advice, diagnoses, or treatment plans. Any suggestions provided are for informational purposes only and MUST be reviewed and approved by your doctor or healthcare team for personalized care."]}
        ])

        # Adjust text_size of chat_history_label when layout width changes
        self.layout.bind(
            width=lambda instance, value: setattr(self.chat_history_label, 'text_size', (value - dp(20), None)))

        # Ensure the text input has focus initially
        Clock.schedule_once(lambda dt: setattr(self.user_input, 'focus', True), 0.5)

        # Variable to store the last generated plan for email functionality
        self.last_generated_plan = ""
        self.original_problem = ""  # Stores the user's initial query

    def set_user(self, username):
        """Sets the logged-in username for the chatbot screen."""
        self.logged_in_user_id = username
        self.chat_history_label.text = f"Hello, {username}! I'm your Type 1 Diabetes support assistant. Remember: these are not medical advice and must be approved by your healthcare team.\n"

    def _update_rect(self, instance, value):
        """
        Updates the size and position of the background rectangle for the main layout.
        """
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _update_button_rect(self, instance, value):
        instance.canvas.before.children[-1].pos = instance.pos
        instance.canvas.before.children[-1].size = instance.size

    def _update_email_button_rect(self, instance, value):
        instance.canvas.before.children[-1].pos = instance.pos
        instance.canvas.before.children[-1].size = instance.size

    def _update_button_color(self, instance, value):
        # Directly use the stored Color instruction reference
        if value == 'down':
            self.send_button_color.rgba = (0.05, 0.25, 0.35, 1)  # Darker blue when pressed
        else:
            self.send_button_color.rgba = (0.1, 0.5, 0.7, 1)  # Blue

    def _update_email_button_color(self, instance, value):
        # Directly use the stored Color instruction reference
        if value == 'down':
            self.send_email_button_color.rgba = (0.05, 0.3, 0.4, 1)  # Darker blue when pressed
        else:
            self.send_email_button_color.rgba = (0.1, 0.6, 0.8, 1)  # Lighter blue

    def update_chat_history(self, message):
        """
        Appends a message to the chat history and scrolls to the bottom.
        """
        self.chat_history_label.text += message + "\n"
        # Ensures the scroll bar always goes to the latest message.
        Clock.schedule_once(lambda dt: setattr(self.scroll_view, 'scroll_y', 0),
                            0.1)  # Small delay to ensure text renders

    def send_message(self, instance):
        """
        Handles sending the user's message to the chatbot.
        """
        print("Kivy App: Send button pressed!")
        user_message = self.user_input.text.strip()
        self.user_input.text = ""

        if not user_message:
            print("Kivy App: User message is empty, not sending.")  # Debug print
            return  # Don't send empty messages

        self.original_problem = user_message  # Store the user's original query

        self.update_chat_history(f"[b]You:[/b] {user_message}")  # Display user message in bold
        self.send_button.disabled = True  # Disable button to prevent multiple sends
        self.user_input.disabled = True  # Disable input during processing
        print(
            f"Kivy App: Input and button disabled. user_input.disabled: {self.user_input.disabled}, send_button.disabled: {self.send_button.disabled}")  # Debug print
        self.update_chat_history("Bot: [i]Thinking...[/i]")  # Indicate that the bot is processing
        print("Kivy App: Starting API call in new thread.")  # Debug print

        # Run the API call in a separate thread to avoid freezing the UI
        threading.Thread(target=self._get_gemini_response, args=(user_message,)).start()

    def _get_gemini_response(self, user_message):
        """
        Makes the API call to Gemini in a separate thread.
        """
        print("Kivy App: Inside _get_gemini_response thread.")
        bot_response = "An unexpected error occurred during processing. Please try again."  # Default error message
        try:
            # Check if API_KEY is set
            if not API_KEY or API_KEY == "YOUR_API_KEY":
                bot_response = "Error: Gemini API Key is not configured. Please set your API_KEY."
                print("Kivy App: Error: API_KEY is not set.")
                return  # Exit early if no API key

            response = self.chat_session.send_message(user_message)
            bot_response = response.text
            self.last_generated_plan = bot_response  # Store the last response for email
            print("Kivy App: Gemini response received.")
        except Exception as e:
            # Enhanced error handling for common API issues
            if "400 Request contains an invalid argument" in str(e):
                bot_response = "Error: Your API key might be invalid or unauthorized. Please check your key and project settings."
            elif "404 models/" in str(e) and "not found" in str(e):
                bot_response = f"Error: The model '{MODEL_NAME}' was not found or is not supported. Please check available models."
            else:
                bot_response = f"An unexpected error occurred: {e}. Please try again."
            print(f"Kivy App: Error during Gemini API call: {e}")
        finally:
            # Always schedule UI update, even if an error occurred
            Clock.schedule_once(lambda dt: self._update_ui_after_response(bot_response))

    def _update_ui_after_response(self, bot_response):
        """
        Updates the UI with the bot's response after the API call completes.
        """
        print("Kivy App: Updating UI after response.")
        # Remove "Bot: Thinking..." and add the actual response
        current_text_lines = self.chat_history_label.text.split('\n')
        # Check if the last line (before the current newline) is "Bot: Thinking..."
        if len(current_text_lines) >= 2 and current_text_lines[-2] == "Bot: [i]Thinking...[/i]":
            current_text_lines[-2] = f"[b]Bot:[/b] {bot_response}"  # Replace with actual response
            self.chat_history_label.text = '\n'.join(current_text_lines)
        else:
            # Fallback if "Thinking" wasn't there (e.g., initial error)
            self.update_chat_history(f"[b]Bot:[/b] {bot_response}")

        self.send_button.disabled = False  # Re-enable button
        self.user_input.disabled = False  # Re-enable input
        print(
            f"Kivy App: Input and button re-enabled. user_input.disabled: {self.user_input.disabled}, send_button.disabled: {self.send_button.disabled}")

        # Ensure focus is set after a very slight delay to allow UI to fully update
        Clock.schedule_once(lambda dt: setattr(self.user_input, 'focus', True), 0.1)

        self.scroll_view.scroll_to(self.chat_history_label)  # Ensure scroll to bottom
        print("Kivy App: UI updated, input re-enabled.")  # Debug print

        # Show email options if a plan was generated.
        # This logic is based on whether last_generated_plan has content.
        if self.last_generated_plan:
            self.email_input.disabled = False
            self.email_input.opacity = 1
            self.send_email_button.disabled = False
            self.send_email_button.opacity = 1
            print("Kivy App: Email options enabled.")

    def send_plan_email(self, instance):
        """
        Initiates the process to open the default email client with a summarized plan.
        """
        doctor_email = self.email_input.text.strip()
        if not doctor_email:
            self.show_popup("Error", "Please enter your doctor's email address.")
            return

        if not self.last_generated_plan:
            self.show_popup("Error", "No plan has been generated yet to send.")
            return

        self.send_email_button.disabled = True
        self.email_input.disabled = True
        self.show_popup("Summarizing", "Summarizing plan for your doctor. Please wait...")

        # Run summarization in a separate thread
        threading.Thread(target=self._get_summarized_plan_and_send_email,
                         args=(doctor_email, self.last_generated_plan, self.original_problem)).start()

    def _get_summarized_plan_and_send_email(self, doctor_email, full_plan_text, original_problem):
        """
        Generates a summary of the plan and then attempts to send the email.
        This runs in a separate thread.
        """
        summarized_data = {"problem": "my Type 1 Diabetes management",
                           "summary": "No summary generated."}  # Default values
        try:
            summarization_model = genai.GenerativeModel(MODEL_NAME)
            summarization_chat = summarization_model.start_chat(history=[])

            # Summarization prompt for structured output and no extra labels
            # Emphasize grammatically correct problem statement and correct insulin adjustment direction
            summarization_prompt = (
                f"Given the user's query: \"{original_problem}\" and the generated Type 1 Diabetes management plan: \"{full_plan_text}\", "
                f"generate a concise problem statement (max 15 words) for a healthcare professional, "
                f"and a professional summary of the plan. "
                f"The problem statement should be a grammatically correct phrase describing the core challenge or topic from the user's query, "
                f"suitable to follow 'I am currently dealing with '. For example, if the query is about a hackathon, the problem could be 'managing Type 1 Diabetes during a hackathon'. "
                f"The summary should focus on the core strategy, any suggested *example* changes to routine, "
                f"general insulin adjustments (e.g., 'illustrative basal decrease of 10-20% for recurring overnight lows', 'illustrative basal increase of 10-20% for prolonged highs'), "
                f"or patterns observed, and long-term management principles. "
                f"Omit immediate, short-term actions (like 'check blood sugar' or 'eat 15g carbs') unless they are part of a broader, significant change. "
                f"Keep the summary concise and professional. "
                f"Crucially, **do NOT include 'Subject:' or 'Body:' labels within the summary itself.** "
                f"Always include the disclaimer about professional review in the summary. "
                f"When including example insulin adjustments in the summary, ensure the direction (increase/decrease) is generally aligned with standard T1D management for the described problem (e.g., decrease for recurring lows, increase for persistent highs).\n"
                f"Output your response strictly in the following JSON format:\n"
                f"```json\n{{\"problem\": \"[Generated problem statement here]\", \"summary\": \"[Generated summary of the plan here]\"}}\n```"
            )

            summary_response = summarization_chat.send_message(summarization_prompt)
            raw_response_text = summary_response.text.strip()
            print(f"Kivy App: Raw summarization response: {raw_response_text}")

            # Attempt to parse JSON
            if raw_response_text.startswith("```json") and raw_response_text.endswith("```"):
                json_string = raw_response_text[len("```json"): -len("```")].strip()
                summarized_data = json.loads(json_string)
            else:
                # Fallback if not in expected JSON format
                print("Kivy App: Summarization response not in expected JSON format. Attempting fallback.")
                # Simple heuristic: try to find "problem" and "summary"
                # This fallback is less reliable but better than nothing
                problem_match = re.search(r'"problem":\s*"(.*?)"', raw_response_text)
                summary_match = re.search(r'"summary":\s*"(.*?)"', raw_response_text, re.DOTALL)

                if problem_match and summary_match:
                    summarized_data = {
                        "problem": problem_match.group(1).strip(),
                        "summary": summary_match.group(1).strip()
                    }
                else:
                    # If no clear delimiters, just use the whole response as summary and generic problem
                    summarized_data = {"problem": "my Type 1 Diabetes management", "summary": raw_response_text}

            print("Kivy App: Plan summarized for email.")

        except Exception as e:
            print(f"Kivy App: Error during summarization or parsing: {e}")
            summarized_data = {
                "problem": "my Type 1 Diabetes management",
                "summary": f"Error summarizing plan: {e}. Please copy the full plan manually from the app."
            }

        # Schedule the email opening on the main thread
        Clock.schedule_once(lambda dt: self._open_email_client_with_summary(
            doctor_email, summarized_data.get("summary", ""), summarized_data.get("problem", "")
        ), 0)

    def _open_email_client_with_summary(self, doctor_email, summarized_plan_text, problem_statement):
        """
        Opens the default email client with the summarized plan.
        This runs on the main thread.
        """
        # Email subject
        subject = f"T1D Plan for Review: {problem_statement.capitalize()}"  # Dynamically set subject

        # Email body
        body = (
            f"Dear Healthcare Team,\n\n"
            f"I am currently dealing with {problem_statement}. "  # Use the extracted problem statement
            f"My T1D Support bot gave me the following suggestions for managing my Type 1 Diabetes. "
            f"Belo is a summary focusing on key aspects for your review and approval. "
            f"The full plan is available in the app if needed.\n\n"
            "--- Summarized Plan from T1D Chatbot ---\n"
            f"{summarized_plan_text}\n"
            "--------------------------------------\n\n"
            "Please let me know your thoughts and any adjustments needed.\n\n"
            "Sincerely,\n"
            "[Your Name - Optional]"
        )

        encoded_body = urllib.parse.quote(body)
        encoded_subject = urllib.parse.quote(subject)

        mailto_link = f"mailto:{doctor_email}?subject={encoded_subject}&body={encoded_body}"

        # Re-check length for the summary
        MAX_MAILTO_LENGTH = 2000
        if len(mailto_link) > MAX_MAILTO_LENGTH:
            self.show_popup(
                "Email Too Long",
                "Even the summarized plan is too long for direct email. "
                "Please copy the summary from this popup and paste it manually into an email."
            )
            # Display the summary in the popup for easy copying
            self.show_popup("Summarized Plan", summarized_plan_text)
            print(
                f"Kivy App: Summarized Mailto link still too long ({len(mailto_link)} chars). Max is {MAX_MAILTO_LENGTH}.")
            self.send_email_button.disabled = False
            self.email_input.disabled = False
            return

        try:
            webbrowser.open(mailto_link)
            self.show_popup("Email Sent",
                            "Your default email client should open with the summarized plan. Please review and send it.")
            print(f"Kivy App: Mailto link opened: {mailto_link}")
        except Exception as e:
            self.show_popup("Error", f"Could not open email client: {e}\nPlease try sending the email manually.")
            print(f"Kivy App: Error opening mailto link: {e}")
        finally:
            self.send_email_button.disabled = False
            self.email_input.disabled = False

    def show_popup(self, title, message):
        """
        Displays a simple Kivy popup message.
        """
        box = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        box.add_widget(Label(text=message, halign='center', valign='middle', size_hint_y=None, height=dp(50)))
        close_button = Button(text="OK", size_hint_y=None, height=dp(40))
        box.add_widget(close_button)
        popup = Popup(title=title, content=box, size_hint=(0.7, 0.4), auto_dismiss=False)
        close_button.bind(on_press=popup.dismiss)
        popup.open()


# Main App Class
class T1DChatbotApp(App):
    def build(self):
        print("Kivy App: build method started.")
        try:
            Window.size = (dp(400), dp(800))
            Window.clearcolor = (0.1, 0.1, 0.1, 1)

            self.screen_manager = ScreenManager()

            self.login_screen = LoginScreen()
            self.chatbot_screen = ChatbotScreen()  # Store reference to chatbot screen

            self.screen_manager.add_widget(self.login_screen)
            self.screen_manager.add_widget(self.chatbot_screen)

            self.screen_manager.current = 'login_screen'

            print("Kivy App: build method finished successfully.")
            return self.screen_manager
        except Exception as e:
            print(f"Kivy App: An error occurred during build: {e}")
            raise

    def on_start(self):
        print("Kivy App: Application started (on_start method).")
        pass

    def on_stop(self):
        print("Kivy App: Application stopping (on_stop method).")
        pass


if __name__ == '__main__':
    T1DChatbotApp().run()

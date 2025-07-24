# HackThe6ix2025
# Inspiration
As a type 1 diabetic, I have lived through the struggles of feeling lost in my type 1 diabetes management, having to wait months for appointments with my healthcare team. Even simple inquiries require multi-email correspondences lasting up to two weeks. This was the inspiration for ASK T1D, a quick, reliable, and accessible intelligent companion solution. ASK T1D simplifies the complexities of Type 1 Diabetes, a disease impacting over 300,000 Canadians.

# What it does
ASK T1D is an AI-powered chatbot designed to assist Type 1 Diabetics with general information and suggest strategies for blood glucose management. Users can securely register and log in via username/password. The chatbot leverages the Gemini API to provide empathetic and informative responses to various T1D-related queries. A key feature is its ability to summarize generated plans into a concise, pre-filled email, allowing users to easily share discussions with their healthcare professionals for personalized review and approval.

# How I built it
The application is built using Kivy for the cross-platform graphical user interface, allowing it to run on various operating systems. The core logic is written in Python. I integrated Firebase Firestore for secure user authentication (username and hashed password storage) and for managing user accounts. The conversational AI capabilities are powered by the Google Gemini API, specifically using the gemini-1.5-flash model. Asynchronous operations, like API calls, are handled using Python's threading module and Kivy's Clock.schedule_once to ensure the UI remains responsive. The email summarization feature uses the Gemini API for intelligent content generation and Python's webbrowser module to open the user's default email client with pre-populated content.

# Challenges I ran into
One significant challenge was managing the Gemini API quota limits, which occasionally led to temporary service interruptions. Another area that required iterative refinement was Kivy's layout management, particularly with positioning and sizing the logo and other elements to ensure they appeared correctly and responsively on different screen sizes. Initial setup of Firebase Admin SDK and ensuring proper serviceAccountKey.json configuration also presented a learning curve. Finally, prompt engineering for the Gemini API was a crucial challenge as the project should ensure the AI provided helpful suggestions, appropriate disclaimers, and professional summaries for email.

# Accomplishments that I'm proud of
I am proud to have developed a functional and empathetic AI chatbot tailored for Type 1 Diabetics. Successfully implementing secure user authentication with Firebase, integrating a powerful generative AI model, and creating the unique AI-powered email summarization feature are significant accomplishments. We're also pleased with the responsive user interface, which ensures a smooth experience even during API calls.

# What I learned
This project opened me to the world of integrating AI models with desktop applications. I learned how to program with the Kivy platform, Firebase Firestore, use the Gemini API to create a tailored chatbot, and Python's webbrowser module for automated email drafting. More specifically, this project pushed me to understand prompt engineering and how to manage asynchronous operations effectively in a UI framework. Most noteworthy, I learned how to utilize APIs and libraries to create a fully functioning web application.

# What's next for ASK T1D
For the future of ASK T1D, I plan to:
- Implement chat history persistence in Firebase Firestore, allowing users to resume conversations.
- Create a separate application for healthcare professionals providing direct approval abilities through the application rather than email.
- Apply for access to the Dexcom API and become an authorized Digital Health Partner to integrate user Dexcom data for more personalized suggestions
- Further enhance the UI/UX with more intuitive navigation, visual feedback, and potentially data visualization features.
- Investigate mobile deployment options to make the app even more accessible on smartphones and tablets.

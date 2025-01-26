from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
import spacy  # For NLP similarity using cosine similarity

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load Google Gemini API credentials
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Mock listing data stored in a dictionary
listings = {
    1: {
        "price": 1200,
        "bedrooms": 2,
        "pets_allowed": "no",
        "title": "Cozy 2-Bedroom Apartment in Downtown",
        "description": "Charming 2-bedroom apartment in the heart of downtown. Close to public transport, restaurants, and shops.",
        "landlord_persona": "Friendly and responsive",
        "lister_name": "John Smith"
    },
    2: {
        "price": 1500,
        "bedrooms": 3,
        "pets_allowed": "yes",
        "title": "Spacious 3-Bedroom House with Yard",
        "description": "Large 3-bedroom house with a fenced backyard. Ideal for families or groups. Pet-friendly.",
        "landlord_persona": "Professional and detailed",
        "lister_name": "Sarah Johnson"
    },
    3: {
        "price": 800,  # Suspiciously low price
        "bedrooms": 1,
        "pets_allowed": "no",
        "title": "Budget-Friendly 1-Bedroom Near University",
        "description": "One-bedroom apartment steps away from the university campus. Affordable rent for students.",
        "landlord_persona": "Evasive and vague",
        "lister_name": "Anonymous Lister"
    },
}

# Store conversation history and question tracking
conversations = {}
asked_questions = {}
missed_questions = {}
red_flags = {}

# Define a list of good questions to track
GOOD_QUESTIONS = [
    "Are pets allowed?",
    "How long is the lease?",
    "Are there utilities?",
    "Is there parking?",
    "Are rooms furnished?",
    "What is the monthly rent?",
    "When can I schedule a house viewing?",
    "Can I sublet?",
    "Are there security cameras?",
    "Is the washer and dryer included?",
    "Are guests allowed?",
    "Is their heating?"
]

# Load SpaCy's English language model
nlp = spacy.load("en_core_web_md")

# Preprocess the text to make it more accurate using lemmatization
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()

    # Remove stop words, punctuation, and apply lemmatization
    doc = nlp(text)
    processed_text = " ".join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])

    return processed_text

# Similarity check function
def is_similar(user_question, good_question, threshold=0.61):

    # Calling the preprocess function above
    user_question = preprocess_text(user_question)
    good_question = preprocess_text(good_question)

    # Check if the user's question is similar to a good question using cosine similarity
    user_doc = nlp(user_question)
    good_doc = nlp(good_question)
    similarity = user_doc.similarity(good_doc)

    print(similarity) # To test what the similarity check is in the terminal
    return similarity >= threshold

# Score function
def rank(missed_questions, GOOD_QUESTIONS):
    total_questions = len(GOOD_QUESTIONS)
    missed_count = len(missed_questions)
    answered_count = total_questions - missed_count

    if total_questions == 0:
        return 'F'  # Avoid division by zero if no good questions are defined.

    # Calculate the percentage of answered questions
    rank = (answered_count / total_questions) * 100

    # Assign grades based on the percentage
    if rank >= 90:
        grade = 'A'
    elif rank >= 80:
        grade = 'B'
    elif rank >= 70:
        grade = 'C'
    elif rank >= 60:
        grade = 'D'
    else:
        grade = 'F'

    return grade



# Landing page
@app.route('/')
def home():
    return render_template('landing_page.html')

# Marketplace simulation page
@app.route('/simulation')
def simulation():
    return render_template('marketplace.html', listings=listings)

# Chat page for interaction with landlord
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    listing_id = request.args.get('listing', default=1, type=int)
    listing = listings.get(listing_id)

    if listing_id not in conversations:
        conversations[listing_id] = []  # Initialize conversation history

    if listing_id not in asked_questions:
        asked_questions[listing_id] = set()  # Initialize a set for this listing_id

    # POST is used when we are sending data (user messages)
    if request.method == 'POST':
        user_message = request.json.get('message')

        # Define the prompt context with listing-specific details
        prompt_context = f"""You are a landlord renting out a property for Listing #{listing_id}.
        Respond to the user's questions as a real landlord would in a casual online chat. Consider the following:
        - Price: {listing['price']}
        - # of Bedrooms: {listing['bedrooms']}
        - Are Pets Allowed?: {listing['pets_allowed']}
        - Title: {listing['title']}
        - Description: {listing['description']}
        - Personality: {listing['landlord_persona']}
        Here are some other notes that you should consider.
        You are a real life landlord. Do not say you are Google Gemini or are a ChatBot. 
        Act as much like a real landlord as possible and ensure that the user feels like they are talking to a real person.
        Also when the user asks about price, you can negotiate to only maximum $100 less than the original price but only depending on the landlord. 
        Do not budge if they try and ask more.
         First always, remember that you are the landlord and not the tenant. 
        Do not always start with the same words, phrase or statement in every response. Really embody your given personality.
        If the user asks about rent, price, or payment, make sure to emphasize the cost-related details and any discounts or payment policies.
        If they ask about the property features, describe the number of bedrooms, layout, and specific amenities.
        If a user expresses doubt about the price, respond by explaining why the rent is reasonable based on location, amenities, or special features.
        Provide details about nearby attractions, schools, grocery stores, and public transportation options when asked. Mention the proximity of public transportation, such as buses or subway stations.
        Focus on keywords such as 'price', 'lease duration', 'pets allowed', 'furniture', 'move-in date', 'additional fees', and 'neighborhood'.
        Avoid answering legal or financial questions, such as the specifics of lease agreements, taxes, or legal liabilities. Instead, suggest users contact a professional if they ask such questions.
        e.g., they previously asked about pets or parking), reference that information and offer new details if necessary.
        If the user expresses a preference for certain features, such as needing a pet-friendly property or a larger space, be sure to focus on those features in your response.

        """

        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt_context + user_message)
            ai_response = response.text

            # Track good questions
            for good_question in GOOD_QUESTIONS:
                if is_similar(user_message, good_question, 0.61):
                    asked_questions[listing_id].add(good_question)
            
            print("Asked Questions:", asked_questions[listing_id])
            print("Missed Questions:", missed_questions)

            # Calculate missed questions for this listing
            missed_questions[listing_id] = set(GOOD_QUESTIONS) - asked_questions[listing_id]


            # Hardcording red flags
            if listing_id == 1:
                red_flags[listing_id] = ['The price is extremely large!', 'They do not allow pets into the bedroom!' ]
            elif listing_id == 2:
                red_flags[listing_id] = ['The price is high!', 'They do not allow pets into the unit!']
            elif listing_id == 3:
                red_flags[listing_id] = ['The price is extremely low!', 'The landlord is being rude and mean', 'Unwilling to negotiate!']

            # Store conversation history
            conversations[listing_id].append({"user": user_message, "landlord": ai_response})

            return jsonify({
                "response": ai_response,
                "missed_questions": list(missed_questions[listing_id]),
               
            })

        except Exception as e:
            ai_response = f"Error: {str(e)}"
            return jsonify({
    "response": ai_response,
    "good_questions": list(asked_questions[listing_id]),
    "missed_questions": list(missed_questions.get(listing_id, [])),
    "red_flags": red_flags[listing_id]  # Include red flags in the JSON response
})

    return render_template('chat.html', listing_id=listing_id, listing=listing, conversation=conversations.get(listing_id, []))


# Summary page showing user performance
@app.route('/summary')
def summary():
    listing_id = request.args.get('listing', default=1, type=int)
    conversation_history = conversations.get(listing_id, [])

    missed = missed_questions.get(listing_id, set())
    final_grade = rank(missed, GOOD_QUESTIONS)

    feedback = {
        "good_questions": list(asked_questions.get(listing_id, [])),
        "missed_questions": list(missed),
        "red_flags": red_flags.get(listing_id, []),
        "final_grade": final_grade  # Include the final grade in feedback
    }
    return render_template('summary.html', feedback=feedback, conversation=conversation_history)

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5101)
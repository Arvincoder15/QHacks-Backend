Challenges We Ran Into:

Backend

A huge challenge in developing Lease Me Before You Go Go was utilising spaCy’s Natural Language Processing (NLP) capabilities to compare user responses with predefined “good” questions. 
The system flagged a user response as "good" if it met a similarity threshold. However, this occasionally led to unrelated questions being incorrectly marked as relevant. 
Fixing this bug required an understanding of how spaCy uses cosine similarity and lots of experimentation!

Accomplishments That We’re Proud Of:

Backend

We are thrilled with how we leveraged Google Gemini to generate accurate responses that resonate with their given persona. After hours of tinkering with specific and personalized querying, 
we managed to produce dynamic interactions between “tenant” and “landlord.” We are also proud of the structure behind identifying which “landlord” we are communicating with. 
Exploiting the basic idea of Python dictionaries allowed us to assign properties to a “landlord” including their name, where the rental is located, and way more.

Why We Used These Technologies:

Backend

Python was the ideal choice for this project because of its extensive collection of libraries related to artificial intelligence. This allowed us to quickly and efficiently build the application using Flask as a web framework. 
We chose Gemini over other AI models because of online reviews promoting its creativity and human-like tone, which proved effective.



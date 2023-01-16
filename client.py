from nltk.corpus import stopwords
from nltk import pos_tag
from nltk.tokenize import word_tokenize
import requests
import jellyfish
import string

STOP_WORDS = set(stopwords.words ('english')) | set(string.punctuation)

def clean_sentence(sentence):
  #tokenize sentence
  tokens = word_tokenize(sentence)
  #remove stop_words
  return " ".join([token for token in tokens if token not in STOP_WORDS])

def get_nouns(sentence):
  # Tokenize the sentence
  tokens = word_tokenize(sentence)

  # POS tagging
  tagged_tokens = pos_tag(tokens) 

  nouns = []
  for token in tagged_tokens:
      if token[1] in ["NN", "NNS"]:
          nouns.append(token[0])
  return nouns

def get_quizes(topic):
  kahoot_search = requests.get(f"https://create.kahoot.it/rest/kahoots/?query={topic}&language=English")

  if kahoot_search.status_code != 200:
    return None

  kahoot_matches = []
  search_data = kahoot_search.json()
  #find kahoot links
  for kahoot in search_data["entities"]:
    kahoot_data = kahoot["card"]

    if kahoot_data["type"] == "quiz" and kahoot_data["number_of_questions"] > 0:
      quiz_uid = kahoot_data["uuid"]

      if quiz_uid not in kahoot_matches:
        kahoot_matches.append(quiz_uid)
  
  return kahoot_matches

def get_surfaces(quiz_uid):
  kahoot_search = requests.get(f"https://create.kahoot.it/rest/kahoots/{quiz_uid}")

  if kahoot_search.status_code != 200:
    return None

  kahoot_data = kahoot_search.json()

  surfaces = []
  for question in kahoot_data["questions"]:
    if question["type"] != "quiz": #skip questions that not contain text
      continue

    #find correct answer
    correct_answer = None
    for choice in question["choices"]:
      #if its not a normal question with text
      if "answer" not in choice:
        break

      if choice["correct"]:
        correct_answer = choice["answer"]

    if correct_answer:
      surfaces.append({
        "text": question["question"],
        "answer": correct_answer
      })

  return surfaces

def lookup(query):
  #get query topics
  cleaned_query = clean_sentence(query)
  query_nouns = get_nouns(cleaned_query)

  print("Searching..")
  #get kahoots by topic
  kahoot_quizes = []
  for topic in query_nouns:
    kahoot_quizes.extend(get_quizes(topic))

  #get kahoot questions/answers
  surfaces = []
  for quiz_index, quiz in enumerate(kahoot_quizes):
    surfaces.extend(get_surfaces(quiz))

  #get query without stopwords

  #find the best surface
  bs = None
  bs_score = float("-inf")

  for surface in surfaces:
    surface_text = clean_sentence(surface["text"])
    surface_similarity = jellyfish.jaro_distance(cleaned_query, surface_text)

    if surface_similarity > bs_score:
      bs_score = surface_similarity
      bs = surface

  return bs, bs_score 

while True:
  query = input(">> ")

  response = lookup(query)
  if not response[0]:
    print("nothing found")
    continue

  match_text = response[0]["text"]
  match_answer = response[0]["answer"]
  match_score = response[1]

  print(f"""
    text: {match_text}
    score: {match_score}
    answer: {match_answer}
  """)
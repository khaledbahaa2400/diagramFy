# Import required libraries
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import spacy
nlp = spacy.load("en_core_web_sm")


# Required Varialbes
candidate_classes = []
attributes = {}
methods = {}
class_hierarchy = {}
classes_set = []
attributes_set = {}
methods_set = {}


# Phase one start
def replace_pronouns_with_first_subject(sentence):
    doc = nlp(sentence)

    # Find the first subject in the sentence
    first_subject = None
    for token in doc:
        if token.dep_ == "nsubj":
            first_subject = token.text
            break

    # Replace pronouns with the first subject
    replaced_sentence = [first_subject if token.text.lower(
    ) in ['he', 'she', 'it', 'him', 'her'] else token.text for token in doc]

    return ' '.join(replaced_sentence)


def replace_subject(sentence):
    sentence = replace_pronouns_with_first_subject(sentence)

    doc = nlp(sentence)
    first_subject = ''
    first_verb = ''
    total = ""

    # Find the first subject in the sentence
    for i, token in enumerate(doc):
        if token.dep_ == "nsubj":
            first_subject = token.text
        elif token.pos_ == "VERB":
            first_verb = token.text
        if first_subject and first_verb and (token.text.lower() in [',', 'and']):
            # Access the next token using the index i + 1
            next_token = doc[i + 1] if i + 1 < len(doc) else None

            if next_token.dep_ == "nsubj" and token.text == ',':
                first_subject = token.text
                total += " ."
                continue

            total += ". " + first_subject + " " + first_verb

        else:
            total += " " + token.text

    return total
# Phase 1 end


# Rule 3 (Not Completed)
def Rule_3_Class(text):
    # Split the text into sentences
    sentences = [sent.text.strip() for sent in nlp(text).sents]

    # Process each sentence with additional filtering
    for sentence in sentences:
        doc = nlp(sentence.lower())  # Lowercase for case-insensitive filtering

        # Skip if specific phrases are present
        if any(phrase in sentence for phrase in ["is-property-of", "is property", "identified by"]):
            continue

        if any(word.pos_ == "ADP" for word in doc):
            for i, token in enumerate(doc):
                # Check if the token is a noun
                if token.pos_ == "NOUN":
                    # Check if the next token is an ADP (but not the last word)
                    if i + 1 < len(doc) and doc[i + 1].pos_ == "ADP" and i + 2 < len(doc):
                        # Ignore noun followed by ADP (not the last word)
                        continue
                    else:
                        candidate_classes.append(token.text)

                # Check if the token is a verb
                elif token.pos_ == "VERB":
                    # Check if the verb has a direct object (DOBJ)
                    if token.dep_ == "ROOT" and token.i + 1 < len(doc) and doc[token.i + 1].dep_ == "dobj":
                        if token.text not in methods:
                            methods[token.text] = []
                        methods[token.text].append(
                            token.text + " " + doc[token.i + 1].text)


# IsA Rule
def identify_classes_from_isa_relationship(text):
    import re
    doc = nlp(text)
    for sentence in doc.sents:
        for word in sentence:
            if (str(sentence).lower().find("is a") != -1):

                # Define a regular expression pattern for 'IsA' relationships
                isa_pattern = re.compile(r'([\w-]+) is a (.+?)\.')
                # Search for 'IsA' relationships in the text
                matches = isa_pattern.findall(text)

                # Create a dictionary to store class hierarchies

                # Process the matches
                for child_class, parent_class in matches:
                    # Store the relationship in the dictionary
                    doc = nlp(parent_class)
                    parent = ""
                    for i in range(0, len(doc)):
                        if doc[i].pos_ == 'NOUN' and str(doc[i].text).lower() != "subclass":
                            parent += doc[i].text

                    if child_class not in class_hierarchy:
                        class_hierarchy[child_class] = {'parent': parent}
                    else:
                        class_hierarchy[child_class]['parent'] = parent

                for child_class, info in class_hierarchy.items():
                    if (child_class not in candidate_classes):
                        candidate_classes.append(child_class)
                    if (info['parent'] not in candidate_classes):
                        candidate_classes.append(info['parent'])


# Noun+Noun Rule
def Noun_plus_Noun_Rule_5(text):
    doc = nlp(text)

    for i in range(1, len(doc)):
        if doc[i-1].pos_ == 'NOUN' and doc[i].pos_ == 'NOUN' and doc[i-1].pos_ == 'NOUN':
            first_noun = doc[i-1].text
            second_noun = doc[i].text

            if second_noun == "attributes":
                continue

            # Check if the first noun is a candidate class
            if first_noun.lower() in candidate_classes:

                if first_noun not in attributes.keys():
                    attributes[first_noun] = []
                attributes[first_noun].append(second_noun)

    for i in range(2, len(doc)):
        if doc[i-2].pos_ == 'NOUN' and doc[i-1].text == '\'s' and doc[i].pos_ == 'NOUN':
            first_noun = doc[i-2].text
            second_noun = doc[i].text

            # Check if the first noun is a candidate class
            if first_noun.lower() in candidate_classes:
                if first_noun not in attributes.keys():
                    attributes[first_noun] = []
                attributes[first_noun].append(second_noun)


# Attributes Rule 2
def attributes_rule_2(sentence):
    words = word_tokenize(sentence)

    class_name = None
    attribute_name = None

    for i in range(len(words) - 1):
        if words[i] == "is" and words[i + 1] == "property":
            class_name = next(
                (c for c in candidate_classes if c == words[i + 3]), None)
            if class_name:
                if class_name not in attributes.keys():
                    attributes[class_name] = []
                attributes[class_name].append(words[i - 1])
        if words[i] == "is-property-of":

            class_name = next(
                (c for c in candidate_classes if c == words[i + 1]), None)
            if class_name:
                if class_name not in attributes.keys():
                    attributes[class_name] = []
                attributes[class_name].append(words[i - 1])

        if words[i] == "identified" and words[i + 1] == "by":

            class_name = next(
                (c for c in candidate_classes if c == words[i - 1]), None)

            if class_name:
                if class_name not in attributes.keys():
                    attributes[class_name] = []
                attributes[class_name].append(words[i + 2])

    if class_name and attribute_name:
        attributes[class_name].append(attribute_name)


# Attributes Rule 3
def attributes_rule_3(doc):
    nlp = spacy.load("en_core_web_sm")

    for word in str(doc).split('.'):
        doc = nlp(word)
        for i, token in enumerate(doc):

            if token.text.lower() == "of" and i-1 >= 0 and i + 1 < len(doc):
                next_token = doc[i + 1].text.lower()
                if next_token in candidate_classes:
                    previous_token = doc[i - 1].text.lower()
                    if next_token not in attributes.keys():
                        attributes[next_token] = []
                    attributes[next_token].append(previous_token)

                if next_token in ["a", "an", "the"] and i + 2 < len(doc):
                    next_token = doc[i + 2].text.lower()
                    if next_token in candidate_classes:
                        previous_token = doc[i - 1].text.lower()
                        if next_token not in attributes.keys():
                            attributes[next_token] = []
                        attributes[next_token].append(previous_token)


# Identify Attributes Rule
def identify_attributes(sentence):
    doc = nlp(sentence)

    # Find the index of "attributes are" in the sentence
    attributes_index = -1
    for i, token in enumerate(doc):

        if i < len(doc) - 2 and token.text.lower() == "attributes" and doc[i + 1].text.lower() == "are":
            attributes_index = i
            break

        if token.pos_ == "PROPN" or token.pos_ == "NOUN":
            candidate = token.text

    # If "attributes are" is found, identify attributes that come after it
    if attributes_index != -1 and candidate in candidate_classes:

        local_attributes = str(doc[attributes_index + 2:]).split(",")
        for i in range(1, len(local_attributes)):
            if str(local_attributes[i]).find("etc") != -1:
                del local_attributes[i]
        if candidate not in attributes.keys():
            attributes[candidate] = []
        for i in local_attributes:
            attributes[candidate].append(i)


# Extract Possesive Nouns
def extract_possessive_nouns(text):
    # Process the input text with SpaCy
    doc = nlp(text)
    sents = list(doc.sents)

    for i in sents:
        # Exclude the last token to avoid index out of range
        doc = nlp(str(i))
        # Exclude the last token to avoid index out of range
        for i, token in enumerate(doc[:]):
            if token.pos_ == "PRON" and token.dep_ == "poss":  # Check for possessive pronoun
                # Find the next noun that the possessive pronoun modifies
                class_name = None
                att = []
                for j in enumerate(doc[:]):
                    if str(j[1]).strip() in candidate_classes:
                        class_name = str(j[1]).strip()
                        break

                if class_name in candidate_classes:

                    if class_name not in attributes.keys():
                        attributes[class_name] = []
                    # Exclude the last token to avoid index out of range
                    for j, token in enumerate(doc[i:]):
                        if token.pos_ == "NOUN":
                            att.append(token.text)
                    for t in att:
                        attributes[class_name].append(str(t))


# Rule 7
def rule_7(text):
    doc = nlp(text)

    for token in doc:
        text = token.text.lower()
        if "_" in text:
            index = text.index("_")
            if text[:index] in candidate_classes:
                if text[:index] not in attributes.keys():
                    attributes[text[:index]] = []
                attributes[text[:index]].append(text[index+1:])


# Has Rule
def has_rule(text):
    for sentence in text.split("."):
        if (str(sentence).find("has") != -1) or (str(sentence).find("have") != -1):
            if len(sentence) > 1:
                arr = str(sentence).split()
                first_noun = arr[0]
                second_noun = arr[len(arr)-1]

                # Check if the first noun is a candidate class
                if first_noun not in attributes.keys():
                    attributes[first_noun] = []
                attributes[first_noun].append(second_noun)


# Methods Rule 1
def methods_rule_1(sentence):
    lexical_verbs = ['do',  'get', 'set', 'make',  'take', 'see', 'look',  'give',
                     'find',  'ask', 'use', 'implement', "extend", "send", "receive", "create"]

    # Define the sentence

    # Process the sentence using Spacy
    doc = nlp(sentence)
    lemmatized_sentence = ' '.join([token.lemma_ for token in doc])
    doc = nlp(lemmatized_sentence)

    # Iterate over the tokens in the doc object

    for sentence in doc.sents:
        subject = None
        verb = False
        for token in sentence:

            if token.pos_ == "VERB" and token.lemma_ in lexical_verbs:
                verb_text = token.text
                verb = True
        if verb == True:
            for token in sentence:
                # Check if the token is a subject
                if token.dep_ == "nsubj":
                    subject = token.text
                elif token.dep_ == "dobj":
                    obj = token.text
                # Check if the token is a verb

        if subject in candidate_classes:

            if subject not in methods.keys():
                methods[subject] = []
            methods[subject].append(verb_text + " " + obj)


# Methods Rule 2
def methods_rule_2(sentence):
    action_verbs = ["run", "write", "clean", "shop", "solve", "build", "create",
                    "read", "update", "delete", "invoke", "call",
                    "compose", "implement", "extend", "send",
                    "receive", "manage", "handle", "connect", "instantiate",
                    "initialize", "access"]

    # Define the sentence

    # Process the sentence using Spacy
    doc = nlp(sentence)
    lemmatized_sentence = ' '.join([token.lemma_ for token in doc])
    doc = nlp(lemmatized_sentence)

    # Iterate over the tokens in the doc object

    for sentence in doc.sents:
        verb = False
        subject = None
        for token in sentence:

            if token.pos_ == "VERB" and token.lemma_ in action_verbs:
                verb_text = token.text
                verb = True
        if verb == True:
            for token in sentence:
                # Check if the token is a subject
                if token.dep_ == "nsubj":
                    subject = token.text
                elif token.dep_ == "dobj":
                    obj = token.text
                # Check if the token is a verb

        if subject in candidate_classes:

            if subject not in methods.keys():
                methods[subject] = []
            methods[subject].append(verb_text + " " + obj)


# Methods Rule 3
def methods_rule_3(sentence):
    # Process the sentence using SpaCy
    doc = nlp(sentence)

    lemmatized_sentence = ' '.join([token.lemma_ for token in doc])
    doc = nlp(lemmatized_sentence)
    # Initialize variables for subject and object

    for sentence in doc.sents:
        subject = None
        obj = None
        verb_phrase = None

    # Extract subject and object from the sentence
        for token in sentence:
            if token.is_punct:
                continue
            if token.dep_ == "nsubj":
                subject = token.text

            elif token.pos_ == "VERB":
                verb_phrase = token.text

            elif token.dep_ == "dobj":
                obj = token.text

        if subject and obj:
            if subject and obj in candidate_classes:

                if subject not in methods.keys():
                    methods[subject] = []
                methods[subject].append(verb_phrase+" " + obj)


# Generation Rule
def generate(text):
    new_text = replace_subject(text)

    Rule_3_Class(new_text)
    identify_classes_from_isa_relationship(new_text)
    Noun_plus_Noun_Rule_5(new_text)
    attributes_rule_2(new_text)
    attributes_rule_3(new_text)
    identify_attributes(text)
    extract_possessive_nouns(new_text)
    rule_7(new_text)
    has_rule(new_text)
    methods_rule_1(new_text)
    methods_rule_2(new_text)
    methods_rule_3(new_text)

    for candidate_class in candidate_classes:
        if candidate_class not in classes_set:
            classes_set.append(candidate_class)

    for key in attributes:
        attributes_set[key] = []
        for value in attributes[key]:
            if str(value).strip() not in attributes_set[key]:
                attributes_set[key].append(str(value).strip())

    for key in methods:
        methods_set[key] = []
        for value in methods[key]:
            if str(value).strip() not in methods_set[key]:
                methods_set[key].append(str(value).strip())

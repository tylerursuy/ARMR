from app import application, db, scheduler, spacy_model
from app.classes import User, Data, Queue
import json
from pathlib import Path
import os
import random
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from spacy.util import minibatch, compounding
import shutil
import speech_recognition as sr

TERMINOLOGY = [
    "history of present illness", "past medical and surgical history",
    "past medical history", "review of systems", "family history",
    "social history", "medications prior to admission",
    "allergies", "physical examination", "electrocardiogram", "impression",
    "recommendations"]


def load_model(model_dir):
    """Takes a file path to model weights and returns a SpaCy model"""
    return spacy.load(model_dir)


def prepare_note(model, text):
    """Output of spaCy text processing containing categories, text, diseases,
        and medications"""
    note_sections = categorize_note(model, text)
    for section in note_sections:
        diseases, medications = parse_entities(model, note_sections[section][
            'text'])
        note_sections[section]['diseases'] = diseases
        note_sections[section]['medications'] = medications
    return note_sections


def categorize_note(model, text):
    """Breakup notes into different sections"""
    categories = {"history of present illness": {"text": "None"},
                  "past medical and surgical history": {"text": "None"},
                  "past medical history": {"text": "None"},
                  "review of systems": {"text": "None"},
                  "family history": {"text": "None"},
                  "social history": {"text": "None"},
                  "medications prior to admission": {"text": "None"},
                  "allergies": {"text": "None"},
                  "physical examination": {"text": "None"},
                  "electrocardiogram": {"text": "None"},
                  "impression": {"text": "None"},
                  "recommendations": {"text": "None"}}
    matcher = PhraseMatcher(model.vocab)
    patterns = [model.make_doc(text) for text in TERMINOLOGY]
    matcher.add("Categories", None, *patterns)
    doc_lower = model(text.lower())
    doc = model(text)
    matches = matcher(doc_lower)
    results = []
    for match_id, start, end in matches:
        span = doc_lower[start:end]
        results.append((span, start, end))
    results = sorted(results, key=lambda tup: tup[1])
    for i in range(len(results)):
        result = results[i]
        next_result = results[i + 1] if i < len(results) - 1 else None
        category = str(result[0])
        start = result[2] if i != 0 else result[2]
        end = next_result[1] if next_result else None
        if end:
            categories[category] = {'text': doc[start:end].text}
        else:
            categories[category] = {'text': doc[start:].text}
    return categories


def parse_entities(model, text):
    """model identifies clinical text from transcribed text"""
    diseases = []
    medications = []
    matcher = Matcher(model.vocab)

    has_method_pattern = [
        {"ENT_TYPE": "CHEMICAL"},
        {"LIKE_NUM": True},
        {"LOWER": "mg"}, {}]
    matcher.add("HasMethod", None, has_method_pattern)

    no_method_pattern = [
        {"ENT_TYPE": "CHEMICAL"},
        {"LIKE_NUM": True},
        {"LOWER": "mg"}]
    matcher.add("NoMethod", None, no_method_pattern)

    just_drug_pattern = [{"ENT_TYPE": "CHEMICAL"}]
    matcher.add("JustDrug", None, just_drug_pattern)

    for entity in model(text).ents:
        if entity.label_ == 'DISEASE':
            diseases.append({'name': str(entity)})

    doc = model(text)
    matches = matcher(doc)
    if matches:
        last_start = None
        last_end = None
        for match_id, start, end in matches:
            string_id = model.vocab.strings[match_id]
            span = doc[start:end]
            if start != last_start and last_start is not None:
                medication = parse_medication(doc[last_start:last_end])
                if '.' not in medication['name']:
                    medications.append(medication)
            last_start = start
            last_end = end
        medication = parse_medication(doc[start:end])
        if '.' not in medication['name']:
            medications.append(parse_medication(doc[start:end]))
    return diseases, medications


def parse_medication(span):
    if len(span) == 4:
        method = None if span[-1].text == '.' else span[-1].text
        return {'name': span[0].text, 'amount': span[1].text,
                'unit': span[2].text, 'method': method}
    elif len(span) == 3:
        method = None if span[-1].text == '.' else span[-1].text
        return {'name': span[0].text, 'amount': span[1].text,
                'unit': span[2].text, 'method': method}
    else:
        return {'name': span[0].text, 'amount': None,
                'unit': None, 'method': None}


def train(model, train_data, output_dir, n_iter=100):
    """Named Entity Recognition Training loop"""
    if model is not None:
        nlp = spacy.load(model)  # load existing spaCy model
        print("Loaded model '%s'" % model)
    else:
        nlp = spacy.blank("en")  # create blank Language class
        print("Created blank 'en' model")

    # create the built-in pipeline components and add them to the pipeline
    # nlp.create_pipe works for built-ins that are registered with spaCy
    if "ner" not in nlp.pipe_names:
        ner = nlp.create_pipe("ner")
        nlp.add_pipe(ner, last=True)
    # otherwise, get it so we can add labels
    else:
        ner = nlp.get_pipe("ner")

    # add labels
    for _, annotations in train_data:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    # get names of other pipes to disable them during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):  # only train NER
        # reset and initialize the weights randomly – but only if we're
        # training a new model
        if model is None:
            nlp.begin_training()
        for itn in range(n_iter):
            random.shuffle(train_data)
            losses = {}
            # batch up the examples using spaCy's minibatch
            batches = minibatch(train_data, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(
                    texts,  # batch of texts
                    annotations,  # batch of annotations
                    drop=0.2,  # dropout - make it harder to memorise data
                    losses=losses,
                )
            print("Losses", losses)

    current_version = output_dir[97:].split(".")[1]
    full_path = output_dir[:97]
    new_version = "0." + str(int(current_version) + 1) + ".0"
    full_path += new_version

    if full_path is not None:
        full_path = Path(full_path)
        if not full_path.exists():
            full_path.mkdir()
        nlp.to_disk(full_path)
        print("Saved model to ", full_path)

    shutil.rmtree(output_dir)
    print("Deleted current model ", output_dir)

    return nlp, full_path


def transcribe(filepath):
    r = sr.Recognizer()
    recording = sr.AudioFile(filepath)
    with recording as source:
        audio = r.record(source)
    talk_to_text = r.recognize_google(audio)
    return talk_to_text


@scheduler.task('interval', id='pipeline', seconds=10)
def process_transcription():
    uploads = Queue.query.filter_by(content=None).order_by(
        Queue.timestamp.asc()).all()
    for upload in uploads:
        if not upload.content:
            filename = upload.filename
            file_dir_path = os.path.join(application.instance_path, 'files')
            file_path = os.path.join(file_dir_path, filename)
            if os.path.exists(file_path):
                talk_to_text = transcribe(file_path)
                os.remove(file_path)
                result = prepare_note(spacy_model, talk_to_text)
                upload.content = json.dumps(result)
                db.session.commit()

import pymongo
from pymongo.errors import PyMongoError
import os 

myclient = pymongo.MongoClient(os.environ.get("MONGODB_URI"))


def get_questions(num_of_questions=5):

    try:
        mydb = myclient["interview-app"]
        questions_collection = mydb["questions"]
        
        questions = list(questions_collection.aggregate([{"$sample": {"size": num_of_questions}}]))
        return questions
        

    except PyMongoError as e:
        print("Error:", e)

    finally:
        myclient.close()
        print("Connection closed.")

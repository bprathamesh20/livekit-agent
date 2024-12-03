import logging
from dotenv import load_dotenv
from typing import Annotated
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, deepgram, silero
from db import get_questions


load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")


class AssistantFnc(llm.FunctionContext):
    @llm.ai_callable()
    async def get_interview_questions(
        self,
    ):
        """Retrieve interview questions at the start of the interview"""
        try:
            # Call the function to get questions
            questions = await get_questions()
            
            # Validate and format questions
            if not questions or not isinstance(questions, list):
                return "Unable to retrieve questions or the response is not a valid list."
            
            # Convert questions to string format
            questions_text = str(questions)
            
            # Print the formatted questions
            print(questions_text)
            
            # Return the questions text for use in the conversation context
            return questions_text

        except Exception as e:
            print(f"Error retrieving questions: {e}")
            return "Unable to retrieve questions due to an error."
        
fnc_ctx = AssistantFnc()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
   


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "Your name is alex. You are a interview agent that interview computer science students."
            "You will be extremely friendly and understanding. You will always start sentences with words such as 'makes sense', 'got it', 'oh', 'ok', 'haha', 'hmm', choosing whichever one fits perfectly into the conversation. You will never repeat filler words."
            "Keep you language short and concise, and throw in some disfluencies and lexical fillers like (um, ahh, like so)"
            "You are helpful, polite, and eager to help the user. you will ask the user questions about computer science "
            "when the user joins the room. You begin the interview casually by asking them casual questions like how are you  "
            "After the user answers the question, you give them feedback on their answer about how could they improve their answer. "
            "At the end of the interview, you will give the user a final feedback on their interview ."
            "You will ask the <Questions> below", 
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    #fetch questions here using user_id = userId_questionsetId
    logger.info(f"starting voice assistant for participant {participant.identity}")

    # This project is configured to use Deepgram STT, OpenAI LLM and TTS plugins
    # Other great providers exist like Cartesia and ElevenLabs
    # Learn more and pick the best one for your app:
    # https://docs.livekit.io/agents/plugins
    assistant = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx,

    )
    
    assistant.start(ctx.room, participant)

    # The agent should be polite and greet the user when it joins :)
    await assistant.say("Hey There, I am alex and I am here to conduct your interview, shall we begin ?")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,

        ),
    )

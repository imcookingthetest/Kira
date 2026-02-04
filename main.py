import asyncio
import threading
import os
from dotenv import load_dotenv

load_dotenv()

from speech_to_text import record_voice, stop_listening_flag
from llm import get_llm_output
from tts import edge_speak, stop_speaking
from ui import JarvisUI
from feedback_sound import play_ding  # NEW: Feedback immediato

from actions.open_app import open_app
from actions.web_search import web_search
from actions.weather_report import weather_action
from actions.whatsapp_action import handle_whatsapp_command
from actions.screen_action import screen_action  

from memory.memory_manager import load_memory, update_memory
from memory.temporary_memory import TemporaryMemory

interrupt_commands = ["mute", "quit", "exit", "stop"]


temp_memory = TemporaryMemory()


async def get_voice_input():
    return await asyncio.to_thread(record_voice)


async def ai_loop(ui: JarvisUI):
    # Initial delay to let UI load
    await asyncio.sleep(0.5)
    
    while True:
        stop_listening_flag.clear()
        from tts import stop_speaking_flag
        stop_speaking_flag.clear()  # Reset TTS flag for new cycle
        
        user_text = await get_voice_input()

        if not user_text:
            continue


        if any(cmd in user_text.lower() for cmd in interrupt_commands):
            stop_speaking()
            temp_memory.reset()
            continue

        # Check for WhatsApp commands (direct handling, bypasses LLM)
        if handle_whatsapp_command(user_text, ui, temp_memory):
            continue

        ui.write_log(f"You: {user_text}")

        # IMMEDIATE FEEDBACK: sound + visual
        play_ding()  # Play notification sound
        ui.start_thinking()  # Show orange pulsing halo


        if temp_memory.get_current_question():
            param = temp_memory.get_current_question()
            temp_memory.update_parameters({param: user_text})
            temp_memory.clear_current_question()
            user_text = temp_memory.get_last_user_text()
        
        temp_memory.set_last_user_text(user_text)

        long_term_memory = load_memory()

        def minimal_memory_for_prompt(memory: dict) -> dict:
            result = {}
            identity = memory.get("identity", {})
            preferences = memory.get("preferences", {})
            relationships = memory.get("relationships", {})
            emotional_state = memory.get("emotional_state", {})

            if "name" in identity:
                result["user_name"] = identity["name"].get("value")

            for k in ["favorite_color", "favorite_food", "favorite_music"]:
                if k in preferences:
                    val = preferences[k].get("value")
                    if isinstance(val, dict) and "value" in val:
                        val = val["value"]
                    result[k] = val

            for rel, info in relationships.items():
                if isinstance(info, dict) and "name" in info and "value" in info["name"]:
                    result[f"{rel}_name"] = info["name"]["value"]

            for event, info in emotional_state.items():
                if "value" in info:
                    result[f"emotion_{event}"] = info["value"]

            return {k: v for k, v in result.items() if v}

        memory_for_prompt = minimal_memory_for_prompt(long_term_memory)
        
        history_lines = temp_memory.get_history_for_prompt()
        recent_history = "\n".join(history_lines.split("\n")[-5:])
        if recent_history:
            memory_for_prompt["recent_conversation"] = recent_history

        if temp_memory.has_pending_intent():
            memory_for_prompt["_pending_intent"] = temp_memory.pending_intent
            memory_for_prompt["_collected_params"] = str(temp_memory.get_parameters())

        try:
            llm_output = get_llm_output(
                user_text=user_text, 
                memory_block=memory_for_prompt
            )
        except Exception as e:
            ui.stop_thinking()  # Stop thinking animation on error
            ui.write_log(f"AI ERROR: {e}")
            continue

        ui.stop_thinking()  # Stop thinking animation when LLM responds

        intent = llm_output.get("intent", "chat")
        parameters = llm_output.get("parameters", {})
        response = llm_output.get("text")
        memory_update = llm_output.get("memory_update")

        if memory_update and isinstance(memory_update, dict):
            update_memory(memory_update)

        temp_memory.set_last_ai_response(response)

        if intent == "open_app":
            app_name = parameters.get("app_name")
            if app_name:
                await asyncio.to_thread(
                    open_app,
                    parameters=parameters,
                    response=response,
                    player=ui,
                    session_memory=temp_memory
                )
            elif response:
                ui.write_log(f"AI: {response}")
                edge_speak(response, ui)

        elif intent == "weather_report":
            city = parameters.get("city")
            time = parameters.get("time")
            if city:
                await asyncio.to_thread(
                    weather_action,
                    parameters=parameters,
                    player=ui,
                    session_memory=temp_memory
                )
            elif response:
                ui.write_log(f"AI: {response}")
                edge_speak(response, ui)

        elif intent == "search":
            query = parameters.get("query")
            if query:
                await asyncio.to_thread(
                    web_search,
                    parameters=parameters,
                    player=ui,
                    session_memory=temp_memory,
                    api_key=os.getenv("SERPAPI_API_KEY")
                )
            elif response:
                ui.write_log(f"AI: {response}")
                edge_speak(response, ui)

        elif intent == "screen_action":
            command = parameters.get("command")
            if command:
                await asyncio.to_thread(
                    screen_action,
                    parameters=parameters,
                    player=ui,
                    session_memory=temp_memory
                )
            elif response:
                ui.write_log(f"AI: {response}")
                edge_speak(response, ui)

        else:
            if response:
                ui.write_log(f"AI: {response}")
                edge_speak(response, ui)

        await asyncio.sleep(0.01)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    face_path = os.path.join(base_dir, "face.png")
    ui = JarvisUI(face_path, size=(900, 900))

    def runner():
        asyncio.run(ai_loop(ui))

    threading.Thread(target=runner, daemon=True).start()
    ui.root.mainloop()


if __name__ == "__main__":
    main()
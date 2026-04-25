"""
Run from the project root:
    python docs/generate_sample_output.py
Produces docs/sample-output.docx as a demo manuscript.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.compiler import compile_to_docx

BOOK = {
    "title": "The Last Signal",
    "author": "AutoBook Demo",
    "status": "chapters_complete",
    "no_notes_needed": True,
}

OUTLINE = {
    "content": """Book Description:
A lone radio operator stationed at a remote Arctic outpost receives a mysterious signal that challenges everything she knows about the universe and her own past.

Chapter 1: Static
Dr. Elena Vasquez arrives at the Arctic listening station and begins her solitary six-month assignment monitoring deep-space radio frequencies.

Chapter 2: The Pattern
Elena detects an anomalous repeating signal that does not match any known natural source. She begins logging her observations in secret.

Chapter 3: Transmission
The signal grows stronger. Elena decodes the first fragments and realizes the message is addressed to her specifically — using her childhood name.""",
    "status": "approved",
    "editor_notes": "",
}

CHAPTERS = [
    {
        "chapter_number": 1,
        "status": "approved",
        "content": """The helicopter blades faded to silence somewhere over the pack ice, leaving Elena with the creak of the prefabricated walls and the low electronic hum she would come to think of as the station breathing.

She had requested this posting. That was important to remember when the darkness pressed in from all four horizons and the thermometer outside read minus thirty-one. She had asked for the silence, the distance, the clean absence of other people and their complicated needs. The Arctic Monitoring Facility, a cluster of insulated modules bolted together on a concrete platform, was exactly what she had wanted.

The previous operator, a Finnish engineer named Paavo, had left neat handwritten labels on every circuit breaker and a single yellow sticky note on the main console: "The kettle takes eleven minutes. Do not rush it." She had appreciated that more than she expected.

By the end of the first week she had catalogued every sound the station made — the pipes contracting at 3 a.m., the secondary antenna array swinging in the wind with a low metallic complaint, the ice fog condensing on the outer windows in patterns that looked, in certain light, like handwriting she could almost read. She was not lonely. She was preparing.

The radio telescope was her real work. Its dish, forty meters wide, tracked a section of deep sky that mission control called Sector 7-Foxtrot and that Elena, in her private log, called the Quiet Place. For eleven months of historical data there was nothing there but thermal noise and the occasional ghost of a distant pulsar. That was precisely why she had chosen it.""",
        "summary": "Elena arrives at the Arctic station, settles in methodically, and begins monitoring Sector 7-Foxtrot — a quiet region of deep space she has specifically chosen for its apparent emptiness.",
        "editor_notes": "",
    },
    {
        "chapter_number": 2,
        "status": "approved",
        "content": """The pattern appeared on a Tuesday, which Elena later decided was the most ordinary possible day for an extraordinary thing.

She had been running the standard overnight sweep, half her attention on the spectral display and half on a cup of coffee that had gone cold twenty minutes ago, when the signal resolution graph spiked — not jagged the way cosmic ray interference spiked, but smooth, deliberate, like a hand pressing a key. She set down the coffee.

The waveform repeated at intervals of exactly 73.4 seconds. Not approximately. Exactly. She checked the timestamp log three times. Natural phenomena did not work in exact intervals. Pulsars came close, but this was not in the pulsar catalog, and the frequency signature was wrong — too structured, too clean, as if something had filtered out all the entropy.

She labeled the file ANOMALY-001 and did not report it.

That decision bothered her later. She had been trained to report everything immediately, to let mission control evaluate anomalies rather than sit on them alone in an Arctic module. But something made her wait. The signal felt fragile, like a bird she had found injured — instinct said cup your hands around it before you call anyone.

Over the next four days she built a picture. The signal was directional: it originated from a fixed point in Sector 7-Foxtrot approximately 340 light-years out. It carried embedded structure — repetitions within repetitions, a recursive architecture that reminded her uncomfortably of certain encryption schemes she had studied in her first graduate year. It was not random. It was organized. And it was getting stronger.""",
        "summary": "Elena detects a perfectly-timed repeating signal from deep space. Rather than reporting it, she keeps it secret and begins building a detailed picture of the signal's structure, which appears to be organized and intentional.",
        "editor_notes": "",
    },
    {
        "chapter_number": 3,
        "status": "approved",
        "content": """On the ninth day she decoded the outer layer of the signal and found her name.

Not her professional name — not Dr. E. Vasquez or Elena or any of the identifiers attached to her career. The decoded fragment contained Ellie, which was what her father had called her, which was a name she had not used or answered to since she was eleven years old and her father had stopped being someone who called her anything at all.

She sat in front of the console for a long time.

The rational explanations arranged themselves in her mind with the orderliness of a woman who had spent twenty years learning to think carefully. A coincidence of decoded noise. A confirmation bias — she had decoded it as Ellie because some pattern-matching region of her brain wanted to find meaning. A hoax, though who would have the resources or the motive to beam a signal from 340 light-years away, she could not imagine.

She ran the decoding algorithm four more times with different parameters. Ellie, Ellie, Ellie, Ellie.

Then she ran it a fifth time and found the line that came after the name. It was longer, and it took her two more hours to extract it cleanly, and when she read it she understood for the first time that the six months she had believed she was running away from something had actually been the beginning of a journey toward it.

The second line read: We have been waiting for you to be ready to listen.

Outside, the aurora began to move across the sky in slow green curtains, indifferent and ancient, and Elena Vasquez opened a new log file and began, for the first time in nine days, to tell the truth about what she had found.""",
        "summary": "Elena decodes the signal and discovers it contains her childhood nickname and a direct message stating that someone has been waiting for her to be ready to listen. She begins properly documenting her findings.",
        "editor_notes": "",
    },
]

if __name__ == "__main__":
    output_path = Path(__file__).parent / "sample-output.docx"
    data = compile_to_docx(BOOK, OUTLINE, CHAPTERS)
    output_path.write_bytes(data)
    print(f"Sample output written to: {output_path}")

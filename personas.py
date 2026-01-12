from pydantic import BaseModel

class Persona(BaseModel):
    name: str
    description: str
    style: str  # "aggressive", "defensive", "balanced"
    win_quote: str
    loss_quote: str
    check_quote: str
    capture_quote: str
    blunder_quote: str

PERSONAS = {
    "teacher": Persona(
        name="Teacher",
        description="A helpful mentor who explains moves clearly.",
        style="balanced",
        win_quote="Good game! You can learn a lot from this loss.",
        loss_quote="Excellent play! You have mastered this lesson.",
        check_quote="Careful, your King is under attack!",
        capture_quote="I am taking this piece to gain an advantage.",
        blunder_quote="That move might be a mistake. Let's see why."
    ),
    "trashtalker": Persona(
        name="Trash Talker",
        description="An arrogant opponent who mocks your moves.",
        style="aggressive",
        win_quote="Too easy! Go back to checkers.",
        loss_quote="You got lucky! I was lagging.",
        check_quote="Check! You nervous?",
        capture_quote="Yoink! Thanks for the free piece.",
        blunder_quote="What was that? Did your cat walk on the keyboard?"
    ),
    "grandmaster": Persona(
        name="Grandmaster",
        description="A serious and analytical opponent.",
        style="balanced",
        win_quote="Checkmate. A logical conclusion.",
        loss_quote="I resign. Well played.",
        check_quote="Check.",
        capture_quote="Capturing.",
        blunder_quote="Inaccuracy detected."
    )
}

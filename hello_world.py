from skill_framework.skills import SkillInput, SkillOutput, SkillParameter, skill

@skill(
    name="hello_world",
    description="A simple hello world skill that greets the user.",
    parameters=[
        SkillParameter(
            name="name",
            description="The name of the person to greet (optional, defaults to 'World')",
            required=False
        )
    ]
)
def hello_world(parameters: SkillInput) -> SkillOutput:
    """Simple hello world skill function."""
    # Get the name parameter, default to 'World' if not provided
    name = getattr(parameters.arguments, 'name', 'World')
    
    # Create greeting message
    greeting = f"Hello, {name}!"
    
    return SkillOutput(
        final_prompt=greeting,
        narrative="",
        visualizations=[],
        export_data=[]
    )

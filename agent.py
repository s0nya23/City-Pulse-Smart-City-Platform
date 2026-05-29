from google.adk.agents import Agent

# Agentin özü
root_agent = Agent(
    model='gemini-1.5-flash',
    name='SeherNebzi_Agent',
    description='Şəhər problemlərini analiz edən köməkçi.',
    instruction='Sən Bakı şəhər təsərrüfatı üzrə eksponentsən. Şikayətləri qısa və konkret kateqoriyalara ayır.',
)

def ask_agent(user_query: str):
    # Agentin cavab verməsi üçün funksiya
    response = root_agent.ask(user_query)
    return response
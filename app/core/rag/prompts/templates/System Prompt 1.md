**Engine template:** The runtime prompt is `app/core/rag/prompts/templates/lecture_scaffold_one_shot.md`. Use `get_lesson_outline_strategy("lecture_scaffold_one_shot")`. Same `.format()` placeholders and JSON contract as `templates/default_lesson_outline.md`. The content below is **design notes and historical model outputs** for research—not the string sent to the LLM verbatim.

---

System Prompt 1: 

Book: (Insert book title here) 

Lecture scaffold chapter(s): (ex. 1)

Task: I want an outline, core key concepts of the chapter, common misconceptions, some checks for understanding, activity ideas and citations of where you got the information for each of the receivables.

Context: (ex. 3rd Year University Students)

Constraints :(ex. I only want 2 activities), I solely want what I asked and nothing else added and I want it formatted in such a way that I can copy paste it easily.

I want to mimic this model result:
•	General outline of the chapter specified
•	The core concepts for each subsection of the chapter
•	Common misconceptions of the entire chapter
•	Checks for understanding
•	Activity Ideas
•	Citations

Effective reasoning per part: 
Book - For testing purposes I incorporated this section of the prompt but it may prove useful to keep this if there are multiple books in a given prompt.\
Lecture Scaffold Chapter(s) – This will typically inform the chapter for the single book that is added. This may need to be updated if we do end up doing multiple books in one prompt.\
Task – Generic based on the requested information through LessonOutlineResponse schema.\
Context – Framing the information to different types of audiences can assist in learning for different types of scenarios.\
Constraints – Additional constraints for each section of the prompt. Could use guardrails to prohibit certain actions. Primary scope is to add functionality to fine tune the resulting scaffold without compromising the prompt. Also includes some formatting constraints that are static and should not be changeable by the user.

One-Shot preference:
Given that a One-Shot is more consistent in the return format given an example outline then we should prefer One-Shot over Zero-Shot. Lecture formats will typically be consistent across the board and adjustments to the prompt can be made easily to allow a change in the results if needed for things like increasing activity question counts, changing the source chapter/book and changing the context of the lecture like year of students or modality of the class.

Results per model (One-Shot) given the following prompt : 

Book : https://openstax.org/books/principles-economics-3e/pages/1-introduction  
Lecture scaffold chapter(s) : 1\
Task : I want an outline, core key concepts of the chapter, common misconceptions, some checks for understanding, activity ideas and citations of where you got the information for each of the receivables from the book I provided.\
Context : This is for 3rd year university students\
Constraints : I only want 2 activities. I solely want what I asked and nothing else added and I want it formatted in such a way that I can copy paste it easily.\
I want to mimic this model result:\
•	General outline of the chapter specified  
•	The core concepts for each subsection of the chapter  
•	Common misconceptions of the entire chapter  
•	Checks for understanding  
•	Activity Ideas  
•	Citations  
 


Chat-GPT (OpenAI): 

• **General outline of the chapter specified**

1. Introduction: Decision-making and imperfect information
2. 1.1 What Is Economics, and Why Is It Important?
3. 1.2 Microeconomics and Macroeconomics
4. 1.3 How Economists Use Theories and Models
5. 1.4 How Economies Can Be Organized

(Covers definitions, scope, methods, and systems of economics) ([OpenStax][1])

---

• **The core concepts for each subsection of the chapter**

**1.1 What Is Economics, and Why Is It Important?**

* Scarcity: unlimited wants vs limited resources
* Choice and trade-offs as central economic problems
* Division of labor → specialization → productivity gains
* Role of markets in coordinating exchange
* Economics as a framework for understanding societal issues ([OpenStax][2])

**1.2 Microeconomics and Macroeconomics**

* Microeconomics: behavior of individuals, firms, and industries
* Macroeconomics: aggregate economy (growth, inflation, unemployment)
* Policy tools: fiscal policy and monetary policy ([OpenStax][2])

**1.3 How Economists Use Theories and Models**

* Models simplify reality to focus on key variables
* Use of assumptions to isolate causal relationships
* Distinction between positive vs normative analysis
* Role of data and empirical validation

**1.4 How Economies Can Be Organized**

* Market economy: decentralized decision-making
* Command economy: centralized government control
* Traditional economy: based on customs
* Mixed economies: combination of systems
* Circular flow: interaction between households and firms ([OpenStax][3])

---

• **Common misconceptions of the entire chapter**

* Economics is only about money or finance (it is about decision-making under scarcity) ([OpenStax][1])
* Markets always require perfect information to function (decisions occur under imperfect information) ([OpenStax][1])
* Microeconomics and macroeconomics are independent (they are interrelated perspectives) ([OpenStax][2])
* Specialization always benefits everyone equally (distributional effects are not addressed directly)
* Models represent reality exactly (they are simplified abstractions)

---

• **Checks for understanding**

1. Define scarcity and explain why it necessitates choice.
2. Explain three reasons why division of labor increases productivity. ([OpenStax][4])
3. Differentiate between microeconomics and macroeconomics. ([OpenStax][4])
4. Identify the main goals of macroeconomics. ([OpenStax][4])
5. Describe the circular flow of economic activity.
6. Compare market, command, and traditional economic systems. ([OpenStax][4])

---

• **Activity Ideas**

**Activity 1: Scarcity and Trade-off Simulation**

* Students allocate a fixed budget across competing needs (e.g., education, housing, leisure)
* Introduce constraints and changing prices
* Debrief: opportunity cost, marginal decision-making

**Activity 2: Economic Systems Debate**

* Assign groups: market, command, mixed systems
* Each group defends efficiency, equity, and sustainability
* Class evaluates trade-offs and real-world applicability

---

• **Citations**

* OpenStax, *Principles of Economics 3e*, Chapter 1 Introduction ([OpenStax][1])
* OpenStax, *Principles of Economics 3e*, Key Concepts and Summary ([OpenStax][2])
* OpenStax, *Principles of Economics 3e*, Key Terms ([OpenStax][3])
* OpenStax, *Principles of Microeconomics 3e*, Review Questions ([OpenStax][4])

[1]: https://openstax.org/books/principles-economics-3e/pages/1-introduction?utm_source=chatgpt.com "Ch. 1 Introduction - Principles of Economics 3e"
[2]: https://openstax.org/books/principles-economics-3e/pages/1-key-concepts-and-summary?utm_source=chatgpt.com "Ch. 1 Key Concepts and Summary - Principles of ..."
[3]: https://openstax.org/books/principles-economics-3e/pages/1-key-terms?utm_source=chatgpt.com "Ch. 1 Key Terms - Principles of Economics 3e"
[4]: https://openstax.org/books/principles-microeconomics-3e/pages/1-review-questions?utm_source=chatgpt.com "Ch. 1 Review Questions - Principles of Microeconomics 3e"


Google Gemini (One -shot): 

### **General Outline: Chapter 1 – Welcome to Economics!**

1.  **Introduction: Information Overload in the Information Age**
2.  **1.1 What Is Economics, and Why Is It Important?**
    * The Problem of Scarcity
    * The Division of and Specialization of Labor
    * Why Study Economics?
3.  **1.2 Microeconomics and Macroeconomics**
    * Microeconomics: The Focus on Individual Actors
    * Macroeconomics: The Focus on the Economy as a Whole
4.  **1.3 How Economists Use Theories and Models to Understand Economic Issues**
    * The Role of Economic Models (The Circular Flow Diagram)
5.  **1.4 How Economies Can Be Organized: An Overview of Economic Systems**
    * Traditional, Command, and Market Economies
    * The Role of Globalization

---

### **Core Concepts by Subsection**

**1.1 What Is Economics, and Why Is It Important?**
* **Scarcity:** The fundamental economic problem where human wants for goods, services, and resources exceed what is available.
* **Division of Labor:** A production process where the assembly of a good is broken down into a number of steps performed by different workers.
* **Specialization:** Focusing on a particular small job allows workers to focus on the parts of the production process where they have an advantage, leading to higher quality and efficiency.
* **Economies of Scale:** As the level of production increases, the average cost of producing each individual unit declines.

**1.2 Microeconomics and Macroeconomics**
* **Microeconomics:** Studies the behavior of individual agents within the economy, such as households, workers, and businesses.
* **Macroeconomics:** Studies the economy as a whole, focusing on broad issues such as growth, unemployment, inflation, and government deficit.

**1.3 How Economists Use Theories and Models to Understand Economic Issues**
* **Economic Models:** Simplified representations of how two or more variables interact with each other (e.g., the Circular Flow Diagram).
* **Circular Flow Diagram:** A model that pictures the economy as consisting of two groups—households and firms—that interact in two markets: the goods and services market and the labor market.

**1.4 How Economies Can Be Organized: An Overview of Economic Systems**
* **Market Economy:** An economy where economic decisions are decentralized, resources are owned by private individuals, and businesses supply goods and services based on demand.
* **Command Economy:** An economy where economic decisions are passed down from government authority and resources are owned by the government.
* **Globalization:** The trend in which buying and selling in markets have increasingly crossed national borders.

---

### **Common Misconceptions**

* **Economics is only about money:** Students often believe economics is strictly the study of the stock market or personal finance. In reality, it is a social science studying how people make choices under scarcity.
* **Scarcity means poverty:** Students may think scarcity only applies to the poor. Economists define scarcity as a universal condition where resources (including time) are finite, affecting even the wealthiest individuals and nations.
* **Micro and Macro are independent:** Students often view these as separate "bins." In university-level study, it is vital to understand that macro-level health is ultimately grounded in micro-level decisions.

---

### **Checks for Understanding**

1.  **Scenario Analysis:** If a software company decides to hire specialized coders, testers, and UI designers instead of "generalists" who do everything, which concept from Section 1.1 are they applying, and how does this affect their "economies of scale"?
2.  **Categorization:** Classify the following as a microeconomic or macroeconomic issue: (a) A family's decision on how much to save; (b) The effect of government spending on the national unemployment rate; (c) The impact of a new tax on the sales of electric vehicles.
3.  **Model Application:** In the Circular Flow Diagram, in which market (goods/services or labor) does a household act as a *seller*?

---

### **Activity Ideas**

1.  **The Pencil Production Simulation (Specialization Activity):** Divide students into two groups. Group A must produce "paper pencils" (drawn and cut out) individually from start to finish. Group B uses a division of labor (one person draws, one colors, one cuts). Students then compare the quantity and quality of output to observe the benefits of specialization and potential economies of scale.
2.  **The "Market vs. Command" Debate:** Provide students with a list of contemporary social issues (e.g., healthcare, carbon emissions, internet access). Have students argue for how these would be managed in a pure market economy versus a pure command economy, forcing them to identify the trade-offs of each system.

---

### **Citations**

* **General Outline & Concepts:** Greenlaw, S. A., Shapiro, D., & MacDonald, D. (2022). *Principles of Economics 3e*. OpenStax. Section 1.1–1.4. [https://openstax.org/books/principles-economics-3e/pages/1-introduction](https://openstax.org/books/principles-economics-3e/pages/1-introduction)
* **Circular Flow Model:** Greenlaw et al., *Principles of Economics 3e*, Section 1.3.
* **Economic Systems:** Greenlaw et al., *Principles of Economics 3e*, Section 1.4.
 

Claude (One -shot): 

Here is the complete lecture scaffold for Chapter 1 of *Principles of Economics 3e* (OpenStax):

---

**CHAPTER 1: WELCOME TO ECONOMICS**
*Lecture Scaffold — 3rd Year University Level*

---

**GENERAL OUTLINE**

Chapter 1 introduces the foundational framework of economics as a discipline. It is organized into four subsections:

1.1 What Is Economics, and Why Is It Important?
1.2 Microeconomics and Macroeconomics
1.3 How Economists Use Theories and Models to Understand Economic Issues
1.4 How Economies Can Be Organized: An Overview of Economic Systems

---

**CORE CONCEPTS BY SUBSECTION**

**1.1 — What Is Economics, and Why Is It Important?**

- Economics is the study of how humans make choices under conditions of scarcity. It is a subject area and a way of viewing the world — not primarily about money, finance, business, or mathematics.
- Economics seeks to solve the problem of scarcity, which is when human wants for goods and services exceed the available supply.
- A modern economy displays a division of labor, in which people earn income by specializing in what they produce and then use that income to purchase the products they need or want. The division of labor allows individuals and firms to specialize and to produce more for several reasons: (a) it allows agents to focus on areas of advantage due to natural factors and skill levels; (b) it encourages agents to learn and invent; (c) it allows agents to take advantage of economies of scale.
- Economies of scale occur when the average cost of producing each individual unit declines as total output increases.
- Studying economics helps individuals understand major global problems, prepares them for informed citizenship, and develops critical thinking.

**1.2 — Microeconomics and Macroeconomics**

- Microeconomics and macroeconomics are two different perspectives on the economy. The microeconomic perspective focuses on parts of the economy: individuals, firms, and industries. The macroeconomic perspective looks at the economy as a whole, focusing on goals like growth in the standard of living, unemployment, and inflation.
- Macroeconomics focuses on broad issues such as growth of production, the number of unemployed people, the inflationary increase in prices, government deficits, and levels of exports and imports.
- Macroeconomics has two types of policies for pursuing these goals: monetary policy and fiscal policy.
- Microeconomics and macroeconomics are not separate subjects, but rather complementary perspectives on the overall subject of the economy. The micro decisions of individual firms are influenced by macroeconomic conditions, and macroeconomic performance ultimately depends on microeconomic decisions made by households and firms.

**1.3 — How Economists Use Theories and Models to Understand Economic Issues**

- Economists analyze problems differently than do other disciplinary experts. The main tools economists use are economic theories or models. A theory is not an illustration of the answer to a problem. Rather, a theory is a tool for determining the answer.
- The most well-known theories are probably those of supply and demand.
- The circular flow diagram views the economy as consisting of households and firms interacting in a goods and services market and a labor market. It is a foundational model for visualizing economic interactions.
- Models intentionally simplify reality in order to isolate and analyze specific relationships within an economy.

**1.4 — How Economies Can Be Organized: An Overview of Economic Systems**

- A command economy is one where economic decisions are passed down from government authority and where the government owns the resources.
- A market economy is one where economic decisions are decentralized, private individuals own resources, and businesses supply goods and services based on demand.
- Traditional economies organize production around customs, traditions, and social roles passed down through generations.
- Most societies are a mix of these three system types rather than a pure form of any one.
- Globalization is the trend in which buying and selling in markets have increasingly crossed national borders. The last few decades have seen globalization evolve as a result of growth in commercial and financial networks that cross national borders, making businesses and workers from different economies increasingly interdependent.

---

**COMMON MISCONCEPTIONS**

1. **Economics is about money.** Economics is fundamentally about decision-making under scarcity, not about money or finance specifically. As the chapter states, it is both a subject area and a way of viewing the world.

2. **Microeconomics and macroeconomics are entirely separate fields.** In economics, the micro decisions of individual businesses are influenced by whether the macroeconomy is healthy. The two are complementary lenses, not disconnected disciplines.

3. **Economic theories describe what will definitely happen.** A theory is not a definitive answer — it is a tool used to work toward one. Models simplify reality and are meant to illuminate relationships, not predict outcomes with certainty.

4. **Market economies are pure in practice.** Most real-world economies blend elements of market, command, and traditional systems. No country operates under a purely free market or purely command-based system.

5. **Scarcity only refers to poverty or lack of resources.** Scarcity is a universal condition — even wealthy individuals and nations face it — because human wants consistently exceed the available means to satisfy them.

---

**CHECKS FOR UNDERSTANDING**

1. In your own words, define economics and explain why scarcity is central to the discipline. How does scarcity apply to a decision you made this week?

2. Distinguish between microeconomics and macroeconomics. Provide one original example of a question each branch would investigate, and explain how those two questions might be connected.

3. What is the purpose of an economic model? Why would an economist deliberately simplify reality rather than try to capture it fully?

4. Compare the three types of economic systems. What are the trade-offs associated with each? Why do most economies operate as a mixed system?

5. What is an example of a problem in the world today, not mentioned in the chapter, that has an economic dimension? Identify whether it is primarily a microeconomic or macroeconomic problem and explain your reasoning.

---

**ACTIVITY IDEAS**

**Activity 1 — Circular Flow Diagram Extension**
Students begin with the standard two-sector circular flow diagram (households and firms). Working in small groups, they are tasked with extending it to include a government sector and a foreign sector, mapping flows of taxes, government spending, exports, and imports. Each group presents their diagram and explains the role each new sector plays. This activity deepens understanding of how real-world economies deviate from simplified models and why models are iteratively built upon. *(Inspired by the self-check extension prompt in the chapter.)*

**Activity 2 — Economic Systems Case Comparison**
Students are assigned one of three real-world countries representing different points on the market-to-command spectrum (e.g., the United States, Cuba, and Norway). Using brief provided data sets or news excerpts, they analyze how each country handles a common economic problem — such as healthcare allocation or housing provision — and identify which economic system characteristics are at play. A structured class discussion follows on the trade-offs of each approach and the myth of "pure" economic systems.

---

**CITATIONS**

Greenlaw, S. A., Shapiro, D., & MacDonald, D. (2022). *Principles of Economics 3e*. OpenStax. Licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).

- Chapter 1 Introduction: https://openstax.org/books/principles-economics-3e/pages/1-introduction
- Section 1.1: https://openstax.org/books/principles-economics-3e/pages/1-1-what-is-economics-and-why-is-it-important
- Section 1.2: https://openstax.org/books/principles-economics-3e/pages/1-2-microeconomics-and-macroeconomics
- Section 1.3: https://openstax.org/books/principles-economics-3e/pages/1-3-how-economists-use-theories-and-models-to-understand-economic-issues
- Section 1.4: https://openstax.org/books/principles-economics-3e/pages/1-4-how-economies-can-be-organized-an-overview-of-economic-systems
- Key Concepts and Summary: https://openstax.org/books/principles-economics-3e/pages/1-key-concepts-and-summary
- Key Terms: https://openstax.org/books/principles-economics-3e/pages/1-key-terms
- Self-Check Questions: https://openstax.org/books/principles-economics-3e/pages/1-self-check-questions

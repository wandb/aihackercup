from mistralai.client import MistralClient

client = MistralClient()


prompt = "hola"*25
prompt = """\n<problem>\n<problem_statement>\n"An apple a day keeps the doctor away" is Steve's motto. His other motto, "You can never have too much of a good thing," holds true for both apples and mottos. Steve would like to eat two apples per day for the next \\(N\\) days, but with strict adherence to his third motto "Consistency is key." Specifically, he'd like the sum of the two apple weights he eats over the next \\(N\\) days to be the same for each day.\nSteve has already purchased \\(2*N-1\\) apples, the \\(i\\)th of which weighs \\(A_i\\) ounces. He\'d like to buy one more apple that\'s as light as possible to fulfill his goal. Steve can buy an apple of any positive integer weight in ounces from the store. Is it possible for him to reach his goal, and if so, what weight apple should he buy?\n{{PHOTO_ID:1563872647765708|WIDTH:600}}\n*The above image depicts the solution to the first sample. Each day, Steve will eat two apples totalling \\(7\\) oz. Steve must buy a \\(4\\) oz apple to make this happen.*\n# Constraints\n\\(1 \\leq T \\leq 70\\)\n\\(1 \\leq N \\leq 3*10^5\\)\nThe sum of \\(N\\) over all cases is at most \\(600{,}000\\)\n\\(1 \\leq A_i \\leq  10^9\\)\n# Input Format\nInput begins with an integer \\(T\\), the number of test cases. Each test case starts with a single integer \\(N\\). The next line contains \\(2*N-1\\) space-separated integers \\(A_1, ..., A_{2*N - 1}\\).\n# Output Format\nFor the \\(i\\)th test case, print "`Case #i:` " followed a single integer, the smallest possible apple weight in ounces that Steve can buy so that he can eat two apples for the next \\(N\\) days and have the sum of apple weights be the same every day, or \\(-1\\) if doing so is impossible.\n# Sample Explanation\nIn the first case, if Steve buys a \\(4\\) oz apple, he can group his apples as shown above. For this input, there\'s no way to succeed by buying any apple below \\(4\\) oz.\nIn the second case, Steve can buy a \\(7\\) oz apple, and eat two apples totaling \\(14\\) oz each day.\nIn the third case, any apple weight will suffice, so Steve will buy the lightest one possible.\nIn the fourth case, no matter what weight apple Steve attempts to buy, it is impossible for him to achieve his goal.\nPlease note, as demonstrated in the seventh case, that it\'s possible for the answer to exceed \\(10^9\\).\n\n</problem_statement>\n<sample_test_cases>\n<sample_input>\n7\n3\n6 3 1 2 5\n2\n7 7 7\n1\n1\n3\n1 9 1 1 4\n4\n1 9 1 1 4 9 9\n4\n1 9 10 1 4 6 9\n3\n1000000000 2 10 4 999999994\n\n</sample_input>\n<sample_output>\nCase #1: 4\nCase #2: 7\nCase #3: 1\nCase #4: -1\nCase #5: 6\nCase #6: -1\nCase #7: 1000000002\n\n</sample_output>\n</sample_test_cases>\n</problem>\n"""

chat_response = client.chat(
    model="open-mistral-nemo",
    messages=[dict(role="system", content="You are a helpful assistant"), 
              dict(role="user", content=prompt)],
    # max_tokens=32
    temperature=0.0
)

all_content = chat_response.choices[0].message.content

print(all_content)
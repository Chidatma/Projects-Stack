import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from llm_helper import llm


def process_posts(raw_file_path, processed_file_path="processed_posts.json"):
    enriched_posts = []

    with open(raw_file_path, encoding="utf-8") as file:
        posts = json.load(file)

    for post in posts:
        metadata = extract_metadata(post["text"])

        # Skip if parsing failed
        if metadata is None:
            print("⚠️ Skipping one post due to parsing failure\n")
            continue

        # Merge dictionaries safely
        post_with_metadata = {**post, **metadata}
        enriched_posts.append(post_with_metadata)

    # Save to file (compact JSON like your screenshot)
    with open(processed_file_path, "w", encoding="utf-8") as outfile:
        json.dump(enriched_posts, outfile, ensure_ascii=False)

    print("\n✅ Processed Posts Output:\n")

    unified_tags = get_unified_tags(enriched_posts)

    for post in enriched_posts:
        current_tags = post['tags']
        new_tags = {unified_tags.get(tag, tag) for tag in current_tags}
        post['tags'] = list(new_tags)

    with open(processed_file_path, "w", encoding="utf-8") as outfile:
        json.dump(enriched_posts, outfile, indent=4)



def get_unified_tags(post_with_metadata):
    unique_tags = set()
    for post in post_with_metadata:
        unique_tags.update(post['tags'])

    unique_tags_list = ','.join(unique_tags)

    template = '''I will give you a list of tags. You need to unify tags with the following requirements,
        1. Tags are unified and merged to create a shorter list.
        Example 1: "Jobseekers", "Job Hunting" can be all merged into a single tag "Job Search".
        Example 2: "Motivation", "Inspiration", "Drive" can be mapped to "Motivation"
        Example 3: "Personal Growth", "Personal Development", "Self Improvement" can be mapped to "Self Improvement
        Example 4: "Scam Alert", "Job Scam" etc. can be mapped to "Scams"
        2. Each tag should be follow title case convention. example: "Motivation", "Job Search"
        3. Output should be a JSON object, No preamble
        3. Output should have mapping of original tag and the unified tag.
        For example: {{"Jobseekers": "Job Search", "Job Hunting": "Job Search", "Motivation": "Motivation}}

        Here is the list of tags:
        {tags}'''
    
    pt = PromptTemplate.from_template(template)
    chain = pt | llm
    parser = JsonOutputParser()

    try:
        response = chain.invoke({"tags": unique_tags_list})
        return parser.parse(response.content)

    except Exception as e:
        print("Failed to unify tags.")
        print("Error:", e)
        print("LLM Output:", response.content if 'response' in locals() else "No response")
        return {}
    

def extract_metadata(post_text):

    template = """
You are given a LinkedIn post.

Extract:
- number of lines
- language (English or Hinglish)
- maximum two tags

Return ONLY valid JSON with exactly three keys:
line_count, language, tags

Post:
{post}
"""

    pt = PromptTemplate.from_template(template)
    chain = pt | llm
    parser = JsonOutputParser()

    try:
        response = chain.invoke({"post": post_text})
        return parser.parse(response.content)

    except Exception as e:
        print("Failed to parse this post.")
        print("Error:", e)
        print("LLM Output:", response.content if 'response' in locals() else "No response")
        return None


if __name__ == "__main__":
    process_posts("data/raw_posts.json","data/processed_posts.json")
import pandas as pd
import re

excel_file_path = 'C:/Users/user/python/Wanted.xlsx'
df = pd.read_excel(excel_file_path)

csv_file_path = 'C:/Users/user/python/Wanted.csv'
df.to_csv(csv_file_path, sep='\t', index=False)

def remove_tags(content):
    
    patterns = ['{.*?}', '<.*?>', '\n', '}', ',']
    combined_pattern = '|'.join(patterns)
    
    cleaned_text = re.sub(combined_pattern, '', content)
    cleaned_text = cleaned_text.replace('\n', ' ')
    formatted_text = re.sub(r'• ', '\n', cleaned_text)
    return formatted_text


txt_file_path = 'C:/Users/user/python/Wanted.txt'

with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        csv_content = csv_file.read()
        cleaned_content = remove_tags(csv_content)
        txt_file.write(cleaned_content)
        
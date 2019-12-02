import torch

CLS_TOKEN = '[CLS]'
SEP_TOKEN = '[SEP]'
PAD_TOKEN = '[PAD]'

flatten = lambda l: [item for sublist in l for item in sublist]


def tokenize_question(example, tokenizer):
    # There exist other tokenizations here (e.g. StanfordNLP). Would be worth to check the differences.
    sub_tokens = list(map(lambda tok: tokenizer.tokenize(tok), example['origin_question_toks']))
    # The flatten is only necessary because the tokenizer returns an array at each step
    # (which makes sense - there could be multiple subwords). The "*" is necessary to "unpack" the list
    question_tokens = [CLS_TOKEN, *flatten(sub_tokens), SEP_TOKEN]
    segment_ids = [0] * len(question_tokens)

    return question_tokens, segment_ids


def tokenize_table_headers(example, tokenizer):
    # the SEP_TOKEN needs to be packed in a list as python can only concat two lists to a new list.
    columns_tokens = list(map(lambda tok: tokenizer.tokenize(tok) + [SEP_TOKEN], example['col_set']))
    columns_tokens = flatten(columns_tokens)
    segment_ids = [0 if tok == SEP_TOKEN else 1 for tok in columns_tokens]

    return columns_tokens, segment_ids


def tokenize_input(batch, label_map, tokenizer, max_length, device):
    all_input_ids = []
    all_attention_mask = []
    all_segment_ids = []
    all_label_ids = []

    for (idx, example) in enumerate(batch):
        question_tokens, question_segment_ids = tokenize_question(example, tokenizer)
        columns_tokens, columns_segment_ids = tokenize_table_headers(example, tokenizer)

        tokens = question_tokens + columns_tokens
        segment_ids = question_segment_ids + columns_segment_ids

        input_ids = tokenizer.convert_tokens_to_ids(tokens)

        attention_mask = [1] * len(tokens)

        label_id = label_map[example['db_id']]

        padd_input(attention_mask, input_ids, max_length, segment_ids)

        all_input_ids.append(input_ids)
        all_attention_mask.append(attention_mask)
        all_segment_ids.append(segment_ids)
        all_label_ids.append(label_id)

    input_ids_tensor = torch.tensor(all_input_ids, dtype=torch.long).to(device)
    attention_mask_tensor = torch.tensor(all_attention_mask, dtype=torch.long).to(device)
    segment_ids_tensor = torch.tensor(all_segment_ids, dtype=torch.long).to(device)
    label_id_tensor = torch.tensor(all_label_ids, dtype=torch.long).to(device)

    return input_ids_tensor, attention_mask_tensor, segment_ids_tensor, label_id_tensor


def padd_input(attention_mask, input_ids, max_length, segment_ids):
    # we don't want to truncate the input - break hard in case it is too long
    assert len(input_ids) <= max_length

    while len(input_ids) < max_length:
        input_ids.append(0)
        attention_mask.append(0)
        segment_ids.append(0)

    assert len(input_ids) == max_length
    assert len(attention_mask) == max_length
    assert len(segment_ids) == max_length
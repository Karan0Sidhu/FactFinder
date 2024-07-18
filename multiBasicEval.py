import json
import ast
from tqdm import tqdm
from jaro import jaro_winkler_metric
import numpy as np
import pandas as pd

DEBUG = False

def compute_metrics_for_excel(file_path, number_of_fails, skip_ranges):
    # Read the Excel file
    df = pd.read_excel(file_path)

    # Convert skip_ranges string to list of tuples
    if skip_ranges:
        skip_ranges = [tuple(map(int, rng.split('-'))) for rng in skip_ranges.split(',')]
    print(skip_ranges)

    # Initialize lists to store scores
    precision_scores = []
    bonus_precision_scores = []
    recall_scores = []
    bonus_recall_scores = []
    f1_scores = []
    bonus_f1_scores = []
    jaro_winkler_scores = []
    bonus_jaro_winkler_scores = []
    f1_bonus_precison_recall_score = []
    false_positive_ratios = []

    count = 0
    # Iterate through each row
    for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing rows"):
        # Skip rows if within skip_ranges
        skip_row = False
        if skip_ranges:
            for rng in skip_ranges:
                if rng[0] <= index + 2 <= rng[1]:
                    skip_row = True
                    break
        if skip_row:
            continue

        count += 1
        output_list = ast.literal_eval(row["Output"])[0]
        ground_truth_list = ast.literal_eval(row["Ground Truth"])[0]
        true_positives_list = ast.literal_eval(row["True Positives"])[0]
        false_positives_list = ast.literal_eval(row["False Positives"])[0]
        false_negatives_list = ast.literal_eval(row["False Negatives"])[0]

        # Check changes to False Positives
        false_positives_temp = []
        bonus_positives_list = []
        decrement_false_negative = 0
        adjustments = ast.literal_eval(row["False Positives Adjustments"])[0]
        if DEBUG:
            print(row["Abstract"])
            print(len(adjustments))
            print(len(false_positives_list))
        if adjustments != []:
            for i in range(len(adjustments)):
                triplet = false_positives_list[i]
                if DEBUG:
                    print(triplet)
                if adjustments[i] == 'fp':
                    false_positives_temp.append(triplet)
                elif adjustments[i] == 'tp':
                    true_positives_list.append(triplet)
                    decrement_false_negative -= 1
                elif adjustments[i] == 'bp':
                    bonus_positives_list.append(triplet)
                else:
                    raise Exception(f"Invalid option: {adjustments[i]}")
            false_positives_list = false_positives_temp

        # Flatten the lists of lists
        ground_truth_flat = [item for sublist in ground_truth_list for item in sublist]
        true_positives_flat = [item for sublist in true_positives_list for item in sublist]
        false_positives_flat = [item for sublist in false_positives_list for item in sublist]
        false_negatives_flat = [item for sublist in false_negatives_list for item in sublist]
        bonus_positives_flat = [item for sublist in bonus_positives_list for item in sublist]
        decrement_false_negative *= 3

        # Compute Original Scores
        # Do initial text to see if ground truth and output is both empty
        scores_list = [precision_scores, recall_scores, f1_scores, jaro_winkler_scores, bonus_precision_scores, bonus_recall_scores, bonus_f1_scores, bonus_jaro_winkler_scores,f1_bonus_precison_recall_score]
        if ground_truth_list == output_list:
            for score_metric in scores_list:
                score_metric.append(1)
        else:
            # Compute precision
            precision = len(true_positives_flat) / (len(true_positives_flat) + len(false_positives_flat)) if (len(true_positives_flat) + len(false_positives_flat)) > 0 else 0
            precision_scores.append(precision)

            # Compute recall
            recall = len(true_positives_flat) / (len(true_positives_flat) + len(false_negatives_flat) + decrement_false_negative) if (len(true_positives_flat) + len(false_negatives_flat) + decrement_false_negative) > 0 else 0
            recall_scores.append(recall)

            # Compute F1-score
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            f1_scores.append(f1)

            # Compute Jaro-Winkler similarity
            jaro_winkler_similarity = jaro_winkler_metric(' '.join(ground_truth_flat), ' '.join(true_positives_flat))
            jaro_winkler_scores.append(jaro_winkler_similarity)

            # Compute Bonus Scores
            # Compute bonus precision
            bonus_precision = (len(true_positives_flat) + len(bonus_positives_flat)) / (len(true_positives_flat) + len(false_positives_flat) + len(bonus_positives_flat)) if (len(true_positives_flat) + len(false_positives_flat) + len(bonus_positives_flat)) > 0 else 0
            bonus_precision_scores.append(bonus_precision)

            # Compute bonus recall
            bonus_recall = (len(true_positives_flat) + len(bonus_positives_flat)) / (len(true_positives_flat) + len(false_negatives_flat) + decrement_false_negative) if (len(true_positives_flat) + len(false_negatives_flat) + decrement_false_negative) > 0 else 0
            bonus_recall_scores.append(bonus_recall)

            # Compute bonus F1-score
            bonus_f1 = (2 * bonus_precision * bonus_recall) / (bonus_precision + bonus_recall) if (bonus_precision + bonus_recall) > 0 else 0
            bonus_f1_scores.append(bonus_f1)

            # Compute bonus Jaro-Winkler similarity
            bonus_jaro_winkler_similarity = jaro_winkler_metric(' '.join(ground_truth_flat), ' '.join(true_positives_flat + bonus_positives_flat))
            bonus_jaro_winkler_scores.append(bonus_jaro_winkler_similarity)

            # Compute bonus precsion and recall F1-score
            f1_bonus_precison_recall = (2 * bonus_precision * recall) / (bonus_precision + recall) if (bonus_precision + recall) > 0 else 0
            f1_bonus_precison_recall_score.append(f1_bonus_precison_recall)

        # Calculate false postive percentage
        false_positive_ratio = len(false_positives_flat) / (len(true_positives_flat) + len(false_positives_flat) + len(bonus_positives_flat)) if (len(true_positives_flat) + len(false_positives_flat) + len(bonus_positives_flat)) > 0 else 0
        false_positive_ratios.append(false_positive_ratio)

    # Compute statistics
    metrics = {
        "Precision": precision_scores,
        "Recall": recall_scores,
        "F1-score": f1_scores,
        "Jaro-Winkler Similarity": jaro_winkler_scores,
        "Bonus Precision": bonus_precision_scores,
        "Bonus Recall": bonus_recall_scores,
        "Bonus F1-score": bonus_f1_scores,
        "Bonus Precision and Recall F1 Score": f1_bonus_precison_recall_score
        # "Bonus Jaro-Winkler Similarity": bonus_jaro_winkler_scores
    }

    print(bonus_recall_scores)

    for metric, scores in metrics.items():
        if number_of_fails > 0:
            fails = [0] * number_of_fails
            scores.extend(fails)
        avg = np.mean(scores)
        minimum = np.min(scores)
        maximum = np.max(scores)
        std = np.std(scores)

        # Print statistics
        print(metric + ":")
        print("  Average:", avg)
        print("  Minimum:", minimum)
        print("  Maximum:", maximum)
        print("  Standard Deviation:", std)
        print()

        if metric == "Jaro-Winkler Similarity":
            print('-' * 20)
            print()

    print("False Positive Percentage: ", np.mean(false_positive_ratios) * 100)
    print()
    print(f"Total Length: {count}")

    file_name = file_path.split(".")[0]

    # Create a text file path by changing the extension
    output_file_path = file_name + ".txt"

    with open(output_file_path, "w") as file:
        for metric, scores in metrics.items():
            if number_of_fails > 0:
                fails = [0] * number_of_fails
                scores.extend(fails)
            avg = np.mean(scores)
            minimum = np.min(scores)
            maximum = np.max(scores)
            std = np.std(scores)

            # Write statistics to the file
            file.write(metric + ":\n")
            file.write("  Average: " + str(avg) + "\n")
            file.write("  Minimum: " + str(minimum) + "\n")
            file.write("  Maximum: " + str(maximum) + "\n")
            file.write("  Standard Deviation: " + str(std) + "\n\n")

            if metric == "Jaro-Winkler Similarity":
                file.write('-' * 20 + "\n\n")
        file.write("False Positive Percentage: " + str(np.mean(false_positive_ratios) * 100) + "\n\n")
        file.write(f"Total Length: {count}")

def manual_evaluation(output_file, ground_truth_file, excel_file):
    # Store data
    all_data = []

    # Iterate through files
    with open(output_file, 'r', encoding="utf-8") as output_file, open(ground_truth_file, "r", encoding="utf-8") as gt_file:
        for output_line, gt_line in tqdm(zip(output_file, gt_file), desc="Reading JSONL", unit=" lines"):
            output_data = json.loads(output_line)
            gt_data = json.loads(gt_line)

            # Read the data
            # if output_data['valid'] == True:
                # output = ast.literal_eval(output_data['output'])
            if True:
                output = output_data['output']
                ground_truth = gt_data['output']

                # Get lists
                true_positives, false_positives, false_negatives = calculate_confusion_lists(output, ground_truth)

                # Prepare data for writing to Excel
                data = {
                    "Abstract": [gt_data['input']],  # Change this to the actual string you want to write
                    "Ground Truth": [ground_truth],
                    "Output": [output],
                    "True Positives": [true_positives],
                    "False Negatives": [false_negatives],
                    "False Positives": [false_positives],
                    "False Positives Adjustments": [['fp' for fp in false_positives]], # Add an empty list for the last column
                    # "False Negatives Adjustments": [['fn' for fn in false_negatives]],
                }

                all_data.append(data)

    # Write data to Excel
    write_to_excel(excel_file, all_data)

def write_to_excel(file_path, all_data):
    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(all_data)

    # Write the DataFrame to an Excel file
    df.to_excel(file_path, index=False)

def calculate_confusion_lists(output, ground_truth):
    # Initate lists
    true_positives = []
    false_positives = []
    false_negatives = []

    # Classify each item
    for triplet_gt in ground_truth:
        found_match = False
        for triplet_out in output:
            # Check if any part of the output triplet partially matches any part of the ground truth triplet
            if (triplet_out[0].lower() in triplet_gt[0].lower()
                and triplet_out[1].lower() in triplet_gt[1].lower()
                and triplet_out[2].lower() in triplet_gt[2].lower()):
                true_positives.append(triplet_gt)
                found_match = True
                break
        if not found_match:
            false_negatives.append(triplet_gt)

    for triplet_out in output:
        found_match = False
        for triplet_gt in ground_truth:
            # Check if any part of the ground truth triplet partially matches any part of the output triplet
            if (triplet_gt[0].lower() in triplet_out[0].lower()
                and triplet_gt[1].lower() in triplet_out[1].lower()
                and triplet_gt[2].lower() in triplet_out[2].lower()):
                found_match = True
                break
        if not found_match:
            false_positives.append(triplet_out)

    return true_positives, false_positives, false_negatives


if __name__ == "__main__":
    # output_file = 'LLama_3/output_80_Llama_3_instruct_Filtered.jsonl'
    # ground_truth_file = "Data/Synthetic_And_Real_Test_Set/test_80.jsonl"
    # excel_file = 'LLama_3/output_80_Llama_3_instruct_Filtered.xlsx'

    # manual_evaluation(output_file, ground_truth_file, excel_file)
##################################################################################################################################################


    edited_excel_file ="fixing_eval_Set\PromptwEg_NoBonusEvaluated.xlsx"
    number_of_fails = 0
    # skip_ranges = "17-26"
    skip_ranges = None
    compute_metrics_for_excel(edited_excel_file, number_of_fails, skip_ranges)
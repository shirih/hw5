import json
from typing import Union, Tuple
import pathlib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import math

class QuestionnaireAnalysis:
    """
    Reads and analyzes data generated by the questionnaire experiment.
    Should be able to accept strings and pathlib.Path objects.
    """

    def __init__(self, data_fname: Union[pathlib.Path, str]):
        self.data_fname = pathlib.Path(data_fname).resolve() 
        if not self.data_fname.exists():
            raise ValueError("Given file doesn't exist.")    

    def read_data(self):
        """Reads the json data located in self.data_fname into memory, to
        the attribute self.data.
        """
        self.data = pd.read_json(self.data_fname)
        
    
    def show_age_distrib(self) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates and plots the age distribution of the participants.

	Returns
	-------
	hist : np.ndarray
	  Number of people in a given bin
	bins : np.ndarray
	  Bin edges
        """
        fig = plt.figure()  
        hist, edges, patches = fig.add_subplot(111).hist(self.data["age"], np.linspace(0, 100, 11))
        return hist, edges

    def remove_rows_without_mail(self) -> pd.DataFrame:
        """Checks self.data for rows with invalid emails, and removes them.

	Returns
	-------
	df : pd.DataFrame
	  A corrected DataFrame, i.e. the same table but with the erroneous rows removed and
	  the (ordinal) index after a reset.
        """
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{1,3})+$'
        for index, row in self.data.iterrows():
            if not re.search(regex,row["email"]):
                self.data.drop(index, inplace=True)
        return self.data.reset_index()

    def fill_na_with_mean(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """Finds, in the original DataFrame, the subjects that didn't answer
        all questions, and replaces that missing value with the mean of the
        other grades for that student.

	Returns
	-------
	df : pd.DataFrame
	  The corrected DataFrame after insertion of the mean grade
	arr : np.ndarray
          Row indices of the students that their new grades were generated
        """ 
        return_df = self.data
        grades_df = self.data.loc[:, "q1":"q5"].stack().unstack(level=0)
        means = grades_df.mean(axis=0)
        _, columns = np.where(grades_df.isna())
        items_with_nans = np.unique(columns)
        print(grades_df.fillna(means[items_with_nans], axis=0))
        return_df.loc[:, "q1":"q5"] = grades_df.fillna(means[items_with_nans], axis=0).stack().unstack(level=0)
        return return_df, items_with_nans 

    def score_subjects(self, maximal_nans_per_sub: int = 1) -> pd.DataFrame:
        """Calculates the average score of a subject and adds a new "score" column
        with it.

        If the subject has more than "maximal_nans_per_sub" NaN in his grades, the
        score should be NA. Otherwise, the score is simply the mean of the other grades.
        The datatype of score is UInt8, and the floating point raw numbers should be
        rounded down.

        Parameters
        ----------
        maximal_nans_per_sub : int, optional
            Number of allowed NaNs per subject before giving a NA score.

        Returns
        -------
        pd.DataFrame
            A new DF with a new column - "score".
        """
        return_df = self.data
        grades_df = self.data.loc[:, "q1":"q5"]
        means = grades_df.mean(axis=1).apply(np.floor).astype('UInt8')
        return_df['score'] = means.values
        for index, row in grades_df.iterrows():
            if row.isna().sum() > maximal_nans_per_sub:
                row['score'] = np.nan
                return_df.at[index] = row
        print(return_df)
        return return_df


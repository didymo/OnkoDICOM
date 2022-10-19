from src.Model.MachineLearningTester import MachineLearningTester

def test_model_machinelearningtester():
    """
    Creates instance of Machine learning tester model
    and tests functions
    """
    model_name="selected_model"

    ml_tester = MachineLearningTester(
            "clinical_data.csv",
            "dvh_data.csv",
            "pyrad_data.csv",
            "path/to/model",
            model_name
        )

    assert ml_tester.get_model_name() == model_name

    ml_tester.predicted_column_name = "target"
    assert ml_tester.get_target() == "target"

    ml_tester.predictions = ["test"]
    assert ml_tester.get_predicted_values() == ["test"]
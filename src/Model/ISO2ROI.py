from skimage import measure

from src.Model.Isodose import get_dose_grid
from src.Model.PatientDictContainer import PatientDictContainer


class ISO2ROI:
    """This class is for converting isodose levels to ROIs."""

    def calculate_boundaries(self):
        """
        Calculates isodose boundaries for each isodose level.
        :return: countours, a list containing the countours for each
                 isodose level
        """
        # Initialise variables needed to find isodose levels
        patient_dict_container = PatientDictContainer()
        pixmaps = patient_dict_container.get("pixmaps")
        slider_min = 0
        slider_max = len(pixmaps)

        rt_plan_dose = patient_dict_container.dataset['rtdose']
        rt_dose_dose = patient_dict_container.get("rx_dose_in_cgray")

        contours = {}

        # Calculate boundaries for each isodose level for each slice
        for slider_id in range(slider_min, slider_max):
            contours[slider_id] = []
            z = patient_dict_container.dataset[slider_id].ImagePositionPatient[2]
            grid = get_dose_grid(rt_plan_dose, float(z))

            isodose_percentages = [10, 25, 50, 75, 80, 85, 90, 95, 100, 105]

            if not (grid == []):
                for sd in isodose_percentages:
                    dose_level = sd * rt_dose_dose / (rt_plan_dose.DoseGridScaling * 10000)
                    contours[slider_id].append(measure.find_contours(grid, dose_level))

        return contours

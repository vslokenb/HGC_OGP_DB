header_template = """
{{ ProjectName }}
LastModified: {{ LastModifiedDate }} {{ LastModifiedTime }}
Runtime: {{ RunDate }} {{ RunTime }}
Component ID: {{ ComponentID }}
Operator: {{ Operator }}
Geometry: {{ Geometry }}
Density: {{ Density }}
Sensor size: {{ SensorSize }}
Flatness: {{ Flatness }}
Position ID: {{ PositionID }}
TrayNo: {{ TrayNo }}
"""

data_template = """
{{FeatureType}} {{FeatureName}}
Point     {{X_coordinate}}    {{Y_coordinate}}    {{Z_coordinate}}
direction cosine:    {{I_coordinate}}    {{J_coordinate}}    {{K_coordinate}}
Radius            {{Radius}}
"""
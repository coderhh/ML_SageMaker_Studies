import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Help methods
def summary_missing_value(inputPath, outputPath):
    '''
    Generate attributes_missing_values reference file 
    
    <INPUT>
    inputPath:  file path of attributes values excel file
    
    <OUTPUT>
    outputPath:  path to save the generated csv file
    '''
    # load the attrbutes values summary .xlsx file
    attributes_values = pd.read_excel(inputPath, sheet_name='Tabelle1')
    # drop first meaningless column
    attributes_values.drop(columns = ['Unnamed: 0'], inplace = True)
    
    # get all attributes names with description and value meaning:
    attributes_names = attributes_values.dropna()[['Attribute','Description','Meaning']]

    # get all attributes with unknow meaning
    attributes_values_unknown = attributes_values[attributes_values.Meaning.isin(['unknown','unknown / no main age detectable'])][['Attribute','Value']]
    
    # there are attributes which is special 'RELAT_AB' 'KBA05_AUTOQUOT' 'CAMEO_DEUG_2015'
    attributes_values_unknown.dropna(inplace=True)
    
    #attributes_values_unknown[attributes_values_unknown.Attribute == 'CAMEO_DEUG_2015'].Value = '-1,X'
    attributes_values_unknown.loc[len(attributes_values_unknown)] = ['RELAT_AB','-1,9']
    
    attributes_values_unknown.loc[len(attributes_values_unknown)] = ['KBA05_AUTOQUOT','-1,9']
    
    # Merge attributes_names with attributes_values_unknown
    attributes_missing_values = pd.merge(attributes_names,attributes_values_unknown,on = ['Attribute'],how = 'outer')
    print(attributes_missing_values.shape)
    # rename the Value column to Missing Value
    attributes_missing_values.rename(columns={"Value": "Missing Value"},inplace=True)
    
    # save 
    attributes_missing_values.to_csv(outputPath,index = None)

def nan_list_func(attribute_name, attributes_missing_values):
    '''
    Get the missing_or_unknown value list from attributes_missing_values.
    
    <INPUT>
    attribute_name: attribute name in attributes_missing_values    
    attributes_missing_values: dateframe contains all attributes and unknown/missing values
    
    <OUTPUT>
    missing_value_list:  the string value list that should be substituted as np.nan
    
    '''
    
    missing_str = str(attributes_missing_values[attributes_missing_values['Attribute'] == attribute_name]['Missing Value'].iloc[0]).replace(' ', '')
    missing_value_list = missing_str.split(',')   
    
    return missing_value_list

def int_float_fix(obj):
    '''
    Purpose: for an object that is float type, return the string integer to assure the substituting process works well.
    For the other types, return the string type. (nan is remain as nan)
    Ex: 
    3.0 -> '3'
    5.0 -> '5'
    nan -> nan
    'XX' -> 'XX'
    2 -> '2'
    
    <INPUT>
    objects with the following types: int, float, str
    
    <OUTPUT>
    str object
    
    '''
    if type(obj) == str or pd.isnull(obj):
        return obj
    else:
        return str(int(obj))

def OST_WEST_KZ_Engineer(x):
    x = str(x)
    if x == 'W':
        return 1
    elif x == "O":
        return 0
    else:
        return np.nan

def PRAEGENDE_JUGENDJAHRE_MOVEMENT_Engineer(x):
    if x in (1,3,5,8,10,12,14):
        return 1
    elif x in (2,4,6,7,11,13,15):
        return 2
    else:
        return np.nan

def PRAEGENDE_JUGENDJAHRE_GENERATION_DECADE_Engineer(x):
    if x in (1,2):
        return 4
    elif x in (3,4):
        return 5
    elif x in (5,6,7):
        return 6
    elif x in (8,9):
        return 7
    elif x in (10,11,12,13):
        return 8
    elif x in (14,15):
        return 9
    else:
        return np.nan        

def WOHNLAGE_RURAL_NEIGBORHOOD_engineer(x):
    if x in (0,1,2,3,4,5):
        return 0
    elif x in (7,8):
        return 1
    else:
        return np.nan

def PLZ8_BAUMAX_PLZ8_BAUMAX_FAMILY_Engineer(x):
    if x in (1,2,3,4):
        return x
    elif x == 5:
        return 0
    else:
        return np.nan

def PLZ8_BAUMAX_PLZ8_BAUMAX_BUSINESS_Engineer(x):
    if x in (1,2,3,4):
        return 0
    elif x == 5:
        return 1
    else:
        return np.nan 

def X_NaN(x):
    if x == 'X':
        return np.nan
    elif np.isnan(float(x)):
        return x
    else:
        return int(x)

def data_preprocess(type, inputfile, attributes_missing_values_file, attributes_type_action_file):
    # check whethere azdias or customer
    
    print('Loading dataset '+ inputfile + '......\n')
    input_df = pd.read_csv(inputfile, sep=';',low_memory=False)
    if type=='customer':
        input_df.drop(columns=['CUSTOMER_GROUP', 'ONLINE_PURCHASE', 'PRODUCT_GROUP'], inplace=True)
    if type == 'mailout':
        response = input_df.RESPONSE
    print('Loading reference file '+ attributes_missing_values_file + '......\n')
    attributes_missing_values = pd.read_csv(attributes_missing_values_file)
    attributes_missing_values_attributes = attributes_missing_values.Attribute.values
    
    print('Replacing missing/unkonwn values with NaNs and drop attributes which are not in description file......\n')
    column_names = input_df.columns.values
    for column_name in column_names:
        if column_name in attributes_missing_values_attributes:
            missing_value_list = nan_list_func(column_name,attributes_missing_values)
            input_df[column_name] = input_df[column_name].map(lambda x: np.nan if int_float_fix(x) in missing_value_list else x)
        else:
            input_df.drop(columns=[column_name], inplace = True)
    print('Replacing X with NaN for attribtue CAMEO_DEUG_2015......\n')
    input_df.CAMEO_DEUG_2015=input_df.CAMEO_DEUG_2015.apply(X_NaN)
    print('Dropping attributes NaN ratio > 0.3.......\n')
    nan_ratio_column_wise = (input_df.isnull().sum() / len(input_df)).sort_values(ascending=False)
    outlier_column_names = nan_ratio_column_wise[nan_ratio_column_wise.values > 0.3].index
    
    # Delete the outlier columns that have more than 30% missing data
    input_df = input_df.drop(outlier_column_names, axis = 1)
    
    print('Loading reference file '+ attributes_type_action_file + '......\n')
    attributes_type_merged_action = pd.read_csv(attributes_type_action_file)
    
    print('Dropping......\n')
    drop_columns = attributes_type_merged_action[attributes_type_merged_action.Action == 'drop'].Attribute.values
    input_df = input_df.drop(columns=drop_columns)
    
    print('Feature engineer: OST_WEST_KZ feature was encoded as 0 for Ost and 1 for West moving pattern.\n')
    input_df.OST_WEST_KZ =  input_df.OST_WEST_KZ.apply(OST_WEST_KZ_Engineer)
    
    print('Feature engineer: PRAEGENDE_JUGENDJAHRE —> MOVEMENT (1: Mainstream, 2: Avantgarde) and GENERATION_DECADE (4: 40s, 5: 50s, 6: 60s, 7: 70s, 8: 80s, 9: 90s)\n')
    movement = input_df.PRAEGENDE_JUGENDJAHRE.apply(PRAEGENDE_JUGENDJAHRE_MOVEMENT_Engineer)
    generation_decade = input_df.PRAEGENDE_JUGENDJAHRE.apply(PRAEGENDE_JUGENDJAHRE_GENERATION_DECADE_Engineer)
    input_df['MOVEMENT'] = movement
    input_df['GENERATION_DECADE'] = generation_decade
    
    print('feature engineer: WOHNLAGE —> RURAL_NEIGBORHOOD (0: Not Rural, 1: Rural)\n')
    rural_neighboorhood = input_df.WOHNLAGE.apply(WOHNLAGE_RURAL_NEIGBORHOOD_engineer)
    input_df['RURAL_NEIGBORHOOD'] = rural_neighboorhood
    
    print('PLZ8_BAUMAX —> PLZ8_BAUMAX_FAMILY (0: 0 families, 1: mainly 1–2 family homes, 2: mainly 3–5 family homes, 3: mainly 6–10 family homes, 4: mainly 10+ family homesand PLZ8_BAUMAX_BUSINESS (0: Not Business, 1: Business)\n')
    family = input_df.PLZ8_BAUMAX.apply(PLZ8_BAUMAX_PLZ8_BAUMAX_FAMILY_Engineer)
    business = input_df.PLZ8_BAUMAX.apply(PLZ8_BAUMAX_PLZ8_BAUMAX_BUSINESS_Engineer)
    input_df['PLZ8_BAUMAX_FAMILY'] = family
    input_df['PLZ8_BAUMAX_BUSINESS'] = business
    input_df = input_df.drop(columns=['PRAEGENDE_JUGENDJAHRE','PLZ8_BAUMAX','WOHNLAGE'])
    

    # get the attribute names which need to be onehot encode, these are categorical attributes from original dataset
    onehot_columns = attributes_type_merged_action[attributes_type_merged_action.Action == 'onehot'].Attribute.values
    # combine with the new categorical attributes from feature engineer
    cat_attributes = list(onehot_columns)
    cat_attributes.extend(('MOVEMENT','GENERATION_DECADE','PLZ8_BAUMAX_FAMILY'))
    cat_attributes = np.array(cat_attributes,dtype='object')

    # get binary columns from the original dataset
    binary_columns = attributes_type_merged_action[attributes_type_merged_action.Type == 'binary'].Attribute.values
    # combine with new binary attributes from feature egineer
    bin_attributes = list(binary_columns)
    bin_attributes.append('PLZ8_BAUMAX_BUSINESS')
    bin_attributes.append('RURAL_NEIGBORHOOD')
    bin_attributes = np.array(bin_attributes,dtype='object')

    num_attributes = attributes_type_merged_action[attributes_type_merged_action.Action.isnull()].Attribute.values
    
    print('Imputing NaN in left attributes......\n')
    for column in input_df.columns:
        if column in cat_attributes:
            input_df[column].fillna(0, inplace=True)
        elif column in bin_attributes:
            input_df[column].fillna(input_df[column].value_counts().index[0], inplace=True)
        elif column in num_attributes:
            input_df[column].fillna(input_df[column].median(), inplace=True)

    print('One hot encoding all categorical attributes......\n')
    # get dummy datafram for all cat_attributes
    dummies = pd.concat([pd.get_dummies(input_df[col],prefix=col) for col in cat_attributes], axis=1)
    # combine with original dataset
    input_df = pd.concat([input_df, dummies], axis=1)
    # drop original cat_attributes
    input_df = input_df.drop(columns=cat_attributes)

    print('Normalizing all num attributes......\n')
    scaler = MinMaxScaler()
    if type=='customer':
        num_attributes = list(num_attributes)
        num_attributes.remove('KKK')
        num_attributes.remove('REGIOTYP')
        num_attributes = np.array(num_attributes,dtype='object')

    
    input_df[num_attributes] = scaler.fit_transform(input_df[num_attributes])
    print('Final cleaned dataset shape: '+ str(input_df.shape))
    if type == 'mailout':
        input_df['RESPONSE'] = response
    return input_df
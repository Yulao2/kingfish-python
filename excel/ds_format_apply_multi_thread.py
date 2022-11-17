"""
@author kingfish
这个代码来源于真实的需求，见/data/joyce/需求文档.md
该实现使用Pandas的函数apply()来遍历DataFrame，并且开启多线程来加速计算
但是该场景是一个CPU密集型场景，python多线程因为GIL的原因，并不能利用到多核加速
"""

import pandas as pd
import xlwings as xw
import time
import math
from threading import Thread

#要处理的文件路径
fpath = "datas/joyce/DS_format_bak.xlsm"

def read_excel():
    #要处理的文件路径
    read_excel_start = time.time()
    #把CP和DS两个sheet的数据分别读入pandas的dataframe
    #cp_df = ds_format_workbook.sheets["CP"].range("A1").options(pd.DataFrame,expand='table',index=False,numbers=float).value
    global cp_df 
    cp_df = pd.read_excel(fpath,sheet_name="CP",header=[0])
    global ds_df 
    ds_df = pd.read_excel(fpath,sheet_name="DS",header=[0,1])
    read_excel_end = time.time()
    print(f"读取excel文件 time cost is :{read_excel_end - read_excel_start} seconds")

    
def save_excel():
    save_excel_start = time.time()
    #保存结果到excel       
    app = xw.App(visible=False,add_book=False)

    ds_format_workbook = app.books.open(fpath)
    ds_format_workbook.sheets["DS"].range("A3").expand().options(index=False).value = ds_df 

    ds_format_workbook.save()
    ds_format_workbook.close()
    app.quit()
    save_excel_end = time.time()
    print(f"保存结果到excel time cost is :{save_excel_end - save_excel_start} seconds") 

def handle_nan(data):
    if math.isnan(data):
        return 0
    return data

#############################################Delta和Loi计算####################################################
delta_item_group_site_set = set()
loi_item_group_site_set = set()


def iner_Iter_From_Cal_loi_Iter_In_Ds(ds_row_k):
    ds_total_capabity1 = ds_row_k[('Total','Capabity.1')]
    if ds_total_capabity1 == 'LOI':
        #相同的item_group+siteid是否计算过
        if (cal_loi_key in loi_item_group_site_set) == False:
            loi_item_group_site_set.add(cal_loi_key)
            LOI_value = handle_nan(ds_row_k[('Current week','BOH')])
            MRP_LOI_value = handle_nan(cal_loi_cp_row['MRP (LOI)'])
            ds_row_k[('Current week','BOH')] = pd.to_numeric(LOI_value,errors='coerce')+ pd.to_numeric(MRP_LOI_value,errors='coerce')
            #print(f"item_group={cal_loi_ds_item_group}的LOI={ ds_row_k[('Current week','BOH')]}")

def Cal_Loi_Iter_In_Ds(ds_row):
     #获取DS表的Item_group值
    global cal_loi_ds_item_group 
    cal_loi_ds_item_group = ds_row[('Total','Capabity')]
        
    if cal_loi_ds_item_group != "" and cal_loi_cp_item_group == cal_loi_ds_item_group :
        index_j = ds_row.name
        iner_iter_df = ds_df.loc[index_j:index_j+5]
        iner_iter_df.apply(iner_Iter_From_Cal_loi_Iter_In_Ds,axis=1)
    

def Cal_Loi_Iter_In_Cp(cp_row):
    global cal_loi_cp_row
    cal_loi_cp_row = cp_row
    #获取CP表的Item_group和siteid值
    global cal_loi_cp_item_group
    cal_loi_cp_item_group = cal_loi_cp_row['Item Group']
    siteid = cal_loi_cp_row['SITEID']
    global cal_loi_key 
    cal_loi_key = cal_loi_cp_item_group + "-" + siteid
    ds_df.apply(Cal_Loi_Iter_In_Ds,axis=1)
    

def iner_Iter_From_Cal_Delta_Iter_In_Ds(ds_row_k):
    ds_total_capabity1 = ds_row_k[('Total','Capabity.1')]
        
    #计算DS表的Delta值
    if ds_total_capabity1 == 'Delta':
    #相同的item_group+siteid是否计算过
        if (cal_delta_key in delta_item_group_site_set) == False:
            delta_item_group_site_set.add(cal_delta_key)
            delta_value = handle_nan(ds_row_k[('Current week','BOH')])
            MRP_LOI_value = handle_nan((cal_delta_cp_row['MRP (LOI)']))
            MRP_OOI_value = handle_nan(cal_delta_cp_row['MRP (OOI)'])
            ds_row_k[('Current week','BOH')] = pd.to_numeric(delta_value,errors='coerce') + pd.to_numeric(MRP_LOI_value,errors='coerce') + pd.to_numeric(MRP_OOI_value,errors='coerce')                        
            #print(f"item_group={cal_delta_ds_item_group}的Delta={ ds_row_k[('Current week','BOH')]}")
    

def cal_Delta_Iter_In_Ds(ds_row):
     #获取DS表的Item_group值
    global cal_delta_ds_item_group 
    cal_delta_ds_item_group = ds_row[('Total','Capabity')]
        
    if cal_delta_ds_item_group != "" and cal_delta_cp_item_group == cal_delta_ds_item_group :
        index_j = ds_row.name
        iner_iter_df = ds_df.loc[index_j:index_j+5]
        iner_iter_df.apply(iner_Iter_From_Cal_Delta_Iter_In_Ds,axis=1)


def cal_delta_iter_in_cp(cp_row):
    global cal_delta_cp_row
    cal_delta_cp_row = cp_row
    #获取CP表的Item_group和siteid值
    global cal_delta_cp_item_group
    cal_delta_cp_item_group = cal_delta_cp_row['Item Group']
    siteid = cal_delta_cp_row['SITEID']
    global cal_delta_key 
    cal_delta_key = cal_delta_cp_item_group + "-" + siteid
    ds_df.apply(cal_Delta_Iter_In_Ds,axis=1)

def clear_Delta(row):
    if row[('Total','Capabity.1')] == 'Delta':
        row[('Current week','BOH')] = 0
        #print(f"清除{row[('Total','Capabity')]}的{row[('Total','Capabity.1')]}的值")

def clear_Loi(row):
    if row[('Total','Capabity.1')] == 'LOI':
        row[('Current week','BOH')] = 0
        #print(f"清除{row[('Total','Capabity')]}的{row[('Total','Capabity.1')]}的值")


#单独进程清除和计算delta的函数
def p_clear_and_cal_delta():
    #先清除Delta的值   
    clear_delta_start = time.time()
    ds_df.apply(clear_Delta,axis=1)
    clear_delta_end = time.time()
    print("清除Delta的值 time cost :",clear_delta_end - clear_delta_start)
    #开始计算Delta值
    cal_delta_start = time.time()
    cp_df.apply(cal_delta_iter_in_cp,axis=1)
    cal_delta_end = time.time()
    print("计算Delta的值 time cost :",cal_delta_end - cal_delta_start)
    print("清除和计算Delta的值 time cost :",cal_delta_end - clear_delta_start)
    #释放数据
    delta_item_group_site_set.clear()

#单独进程清除和计算loi的函数
def p_clear_and_cal_loi():
    #先清除loi的值
    clear_loi_start = time.time()
    ds_df.apply(clear_Loi,axis=1)
    clear_loi_end = time.time()
    print("清除Loi的值 time cost :",clear_loi_end - clear_loi_start)
    #开始计算loi
    cal_loi_start = time.time()
    cp_df.apply(Cal_Loi_Iter_In_Cp,axis=1)
    cal_loi_end = time.time()
    print("计算Loi的值 time cost :",cal_loi_end - cal_loi_start)
    print("清除和计算Loi的值 time cost :",cal_loi_end - clear_loi_start)
    #释放数据
    loi_item_group_site_set.clear()
    
######################################################Delta和Loi计算################################################


####################################################Demand和Supply计算##################################################

def clear_Demand_Iter_In_Ds(ds_row):
   
    ds_total_capabity1 = ds_row[('Total','Capabity.1')]
       
    if ds_total_capabity1 == "Demand":
        #遍历ds的日期列
        for k in range(5,len(ds_df.columns)):
            #获取DS表的日期值
            ds_month = ds_df.columns.get_level_values(0)[k]
            ds_datetime = ds_df.columns.get_level_values(1)[k]
            if clear_demand_cp_datetime == ds_datetime:
                ds_row[(f'{ds_month}',f'{ds_datetime}')] = 0
                #print(f"清除{ds_row[('Total','Capabity')]}的{ds_total_capabity1}的日期{ds_datetime}的值")

def clear_demand():
    for i in range(54,len(cp_df.columns)): 
        #获取cp表的日期值
        global clear_demand_cp_datetime
        clear_demand_cp_datetime = cp_df.columns[i]
        ds_df.apply(clear_Demand_Iter_In_Ds,axis=1)

def clear_Supply_Iter_In_Ds(ds_row):
   
    ds_total_capabity1 = ds_row[('Total','Capabity.1')]
       
    if ds_total_capabity1 == "Supply":
        #遍历ds的日期列
        for k in range(5,len(ds_df.columns)):
            #获取DS表的日期值
            ds_month = ds_df.columns.get_level_values(0)[k]
            ds_datetime = ds_df.columns.get_level_values(1)[k]
            if clear_supply_cp_datetime == ds_datetime:
                ds_row[(f'{ds_month}',f'{ds_datetime}')] = 0
                #print(f"清除{ds_row[('Total','Capabity')]}的{ds_total_capabity1}的日期{ds_datetime}的值")
    

def clear_supply():
    for i in range(54,len(cp_df.columns)): 
        #获取cp表的日期值
        global clear_supply_cp_datetime
        clear_supply_cp_datetime = cp_df.columns[i]
        ds_df.apply(clear_Supply_Iter_In_Ds,axis=1)


def cal_Demand_Iter_Cp(cp_row):
    cp_measure = cp_row['Measure']
    global cal_demand_cp_item_group 
    cal_demand_cp_item_group = cp_row['Item Group']
    global cal_demand_cp_row
    cal_demand_cp_row = cp_row
    if cp_measure == "Total Publish Demand":
        ds_df.apply(cal_Demand_Iter_Ds,axis=1)

def cal_demand():
    cp_df.apply(cal_Demand_Iter_Cp,axis=1)

def cal_demand_Inner_Iter_Ds(inner_iter_ds_row):
    if inner_iter_ds_row[('Total','Capabity.1')] == "Demand":
        for k in range(54,len(cp_df.columns)):
            for m in range(5,len(ds_df.columns)):
                #如果日期相同
                cp_datetime = cp_df.columns[k]
                ds_datetime = ds_df.columns.get_level_values(1)[m]
                ds_month = ds_df.columns.get_level_values(0)[m]
                if cp_datetime == ds_datetime:
                    inner_iter_ds_row[(f'{ds_month}',f'{ds_datetime}')] =  handle_nan(pd.to_numeric(inner_iter_ds_row[(f'{ds_month}',f'{ds_datetime}')],errors='coerce')) + handle_nan(pd.to_numeric(cal_demand_cp_row[f'{cp_datetime}'],errors='coerce'))
                    #print(f"{cal_demand_cp_item_group}的{inner_iter_ds_row[('Total','Capabity.1')]}的值={inner_iter_ds_row[(f'{ds_month}',f'{ds_datetime}')]}")

def cal_Demand_Iter_Ds(ds_row):
    #如果cp和ds的item_group值相同
    ds_item_group = ds_row[('Total','Capabity')]
    if cal_demand_cp_item_group == ds_item_group:
        #从ds该行往下取4行作为一个slice进行处理
        index_j = ds_row.name
        iner_iter_df = ds_df.loc[index_j:index_j+4]
        iner_iter_df.apply(cal_demand_Inner_Iter_Ds,axis=1)

def cal_Supply_Iter_Cp(cp_row):
    cp_measure = cp_row['Measure']
    global cal_supply_cp_item_group 
    cal_supply_cp_item_group = cp_row['Item Group']
    global cal_supply_cp_row
    cal_supply_cp_row = cp_row
    if cp_measure == "Total Commit" or cp_measure == "Total Risk Commit":
        ds_df.apply(cal_Supply_Iter_Ds,axis=1)

def cal_supply():
    cp_df.apply(cal_Supply_Iter_Cp,axis=1)

def cal_supply_Inner_Iter_Ds(inner_iter_ds_row):
    if inner_iter_ds_row[('Total','Capabity.1')] == "Supply":
        for k in range(54,len(cp_df.columns)):
            for m in range(5,len(ds_df.columns)):
                #如果日期相同
                cp_datetime = cp_df.columns[k]
                ds_datetime = ds_df.columns.get_level_values(1)[m]
                ds_month = ds_df.columns.get_level_values(0)[m]
                if cp_datetime == ds_datetime:
                    inner_iter_ds_row[(f'{ds_month}',f'{ds_datetime}')] =  handle_nan(pd.to_numeric(inner_iter_ds_row[(f'{ds_month}',f'{ds_datetime}')],errors='coerce')) + handle_nan(pd.to_numeric(cal_supply_cp_row[f'{cp_datetime}'],errors='coerce'))
                    #print(f"{cal_supply_cp_item_group}的{inner_iter_ds_row[('Total','Capabity.1')]}的值={inner_iter_ds_row[(f'{ds_month}',f'{ds_datetime}')]}")
            
def cal_Supply_Iter_Ds(ds_row):
    #如果cp和ds的item_group值相同
    ds_item_group = ds_row[('Total','Capabity')]
    if cal_supply_cp_item_group == ds_item_group:
        #从ds该行往下取4行作为一个slice进行处理
        index_j = ds_row.name
        iner_iter_df = ds_df.loc[index_j:index_j+4]
        iner_iter_df.apply(cal_supply_Inner_Iter_Ds,axis=1)

#单独进程清除和计算demand的函数
def p_clear_and_cal_demand():
    #先清除Demand各个日期的值
    clear_demand_start = time.time()
    clear_demand()
    clear_demand_end = time.time()
    print(f"DS表Demand的清空总共 time cost is :{clear_demand_end - clear_demand_start} seconds")
    #计算Demand各个日期的值
    cal_demand_start = time.time()
    cal_demand()
    cal_demand_end = time.time()
    print(f"计算DS表的Demand的值 time cost is :{cal_demand_end - cal_demand_start} seconds")

#单独进程清除和计算supply的函数
def p_clear_and_cal_supply():
    #先清除Supply各个日期的值
    clear_supply_start = time.time()
    clear_supply()
    clear_supply_end = time.time()
    print(f"DS表Supply的清空总共 time cost is :{clear_supply_end - clear_supply_start} seconds")
    #计算Supply各个日期的值
    cal_supply_start = time.time()
    cal_supply()
    cal_supply_end = time.time()
    print(f"计算DS表的Supply的值 time cost is :{cal_supply_end - cal_supply_start} seconds")
    
    
######################################################Demand和Supply计算################################################ 

if __name__ == "__main__":
    
    app_start = time.time()
    #读取excel数据到内存
    read_excel()
    
    #开启四个线程开始计算
    cal_start = time.time()
    t_cal_delta = Thread(target=p_clear_and_cal_delta,args=())
    t_cal_delta.start()
    
    t_cal_loi = Thread(target=p_clear_and_cal_loi,args=())
    t_cal_loi.start()
    
    t_cal_demand = Thread(target=p_clear_and_cal_demand,args=())
    t_cal_demand.start()
    
    t_cal_supply = Thread(target=p_clear_and_cal_supply,args=())
    t_cal_supply.start()
    
    t_cal_delta.join()
    t_cal_loi.join()
    t_cal_demand.join()
    t_cal_supply.join()
    
    cal_end = time.time()
    print(f"ds_format python 脚本（使用多线程apply）内存计算总共 time cost is :{cal_end - cal_start} seconds") 
    
    #内存数据写入excel
    save_excel()
    
    app_end = time.time()
    print(f"ds_format python 脚本（使用多进程apply）总共 time cost is :{app_end - app_start} seconds")
    
    
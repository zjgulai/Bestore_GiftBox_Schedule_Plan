# -*- coding: utf-8 -*-
# @Time    : 2022-08-21 15:55
# @Author  : zhou_jian.Pray
# @FileName: model.py
# @Software: PyCharm

import pandas as pd
from gurobipy import tupledict
import itertools
import copy


# TODO 很多函数 return 0的问题需要逐个排查


def get_demand(df, i_d, pack, n, k, s_t, o_t, flag=3):
    '''
    返回需求计划总量num(flag==3代表7天，flag等于0,1代表13周)
    :param df: 订单的DataFrame
    :param i_d: 订单id
    :param pack: 礼盒编码
    :param n: 渠道编码
    :param k: 仓库
    :param s_t: 需求提报时间
    :param o_t: 需求到货时间
    :return: 需求计划数量
    '''
    if flag == 3:
        if df[(df['id'] == i_d) &
              (df['package'] == pack) &
              (df['n'] == n) &
              (df['warehouse'] == k) &
              (df['s_t'] == s_t) &
              (df['o_t'] == o_t)]['num'].size == 0:
            return 0
        else:
            return df[(df['id'] == i_d) &
                      (df['package'] == pack) &
                      (df['n'] == n) &
                      (df['warehouse'] == k) &
                      (df['s_t'] == s_t) &
                      (df['o_t'] == o_t)]['num'].sum()
    else:
        if df[(df['id'] == i_d) &
              (df['package'] == pack) &
              (df['n'] == n) &
              (df['warehouse'] == k) &
              (df['s_t'] == s_t) &
              (df['o_t'] == o_t) &
              (df['flag'] == flag)]['num'].size == 0:
            return 0
        else:
            return df[(df['id'] == i_d) &
                      (df['package'] == pack) &
                      (df['n'] == n) &
                      (df['warehouse'] == k) &
                      (df['s_t'] == s_t) &
                      (df['o_t'] == o_t) &
                      (df['flag'] == flag)]['num'].sum()


def get_inventory(df, warehouse, sample):
    '''
    获取仓库库存
    :param df: 初始库存DataFrame
    :param warehouse: 仓库ID
    :param sample: 子件ID
    :return: 初始库存量
    '''
    if df[(df['warehouse'] == warehouse) & (df['sample'] == sample)]['num'].size == 0:
        return 0
    else:
        return df[(df['warehouse'] == warehouse) & (df['sample'] == sample)]['num'].sum()


def get_trans(df, warehouse, sample, t):
    '''
    13周独有的函数,返回调拨在途数量
    :param df: 调拨信息DataFrame
    :param warehouse: 调拨目的仓库ID
    :param sample: 调拨自己ID
    :param t: 调拨到达时间
    :return: 调拨数量
    '''
    if df[(df['warehouse'] == warehouse) &
          (df['sample'] == sample) &
          (df['t'] == t)]['num'].size == 0:
        return 0
    else:
        return df[(df['warehouse'] == warehouse)
                  & (df['sample'] == sample)
                  & (df['t'] == t)]['num'].sum()


def get_arr(df, warehouse, sample, t):
    '''
    获取到货数据
    :param df: 到货数量DataFrame
    :param warehouse: 到货仓库
    :param sample: 到货子件
    :param t: 到货日期
    :return: 到货数量
    '''
    if df[(df['warehouse'] == warehouse) & (df['sample'] == sample) & (df['t'] == t)]['num'].size == 0:
        return 0
    else:
        return df[(df['warehouse'] == warehouse) & (df['sample'] == sample) & (df['t'] == t)]['num'].sum()


def get_bom(df, pack, sample):
    '''
    获取BOM信息
    :param df: BOM对应的DataFrame
    :param pack: 礼盒id
    :param sample: 子件id
    :return: 礼盒BOM中包含的子件数量
    '''
    if df[(df['pack'] == pack) & (df['sample'] == sample)]['num'].size == 0:
        return 0
    else:
        return df[(df['pack'] == pack) & (df['sample'] == sample)]['num'].values[0]


def supply_c(s, t):
    '''
    返回供应商产能，暂时不处理
    '''
    return 100000


def warehouse_s(df, k, m):
    '''
    返回仓库分装礼盒的速度
    :param df: 分装速度对应的DataFrame
    :param k: 仓库id
    :param m: 礼盒id
    :return: 该仓库分装该礼盒的速度
    '''
    if df[(df['warehouse'] == k) &
          (df['package'] == m)]['num'].size == 0:
        return 0.0001
    else:
        return df[(df['warehouse'] == k) &
                  (df['package'] == m)]['num'].mean()


def warehouse_c(df, k, t):
    '''
    返回仓库的工时数
    :param df: 工时对应的DataFrame
    :param k: 仓库id
    :param t: 分装日期
    :return:  该仓库该天的工时
    '''
    if df[(df['warehouse'] == k) &
          (df['t'] == t)].size == 0:
        return 0
    else:
        return df[df['warehouse'] == k]['hours'].values[0]


def weight(df, m, n):
    if df[(df['package'] == m) & (df['n'] == n)]['w'].size == 0:
        return 0
    else:
        return df[(df['package'] == m) & (df['n'] == n)]['w'].values[0]


def sum_range(num1, begin, end):
    '''
    将[begin， end]区间中大于numl的值提取到l_end list中返回
    :param num1:
    :param begin:
    :param end:
    :return:
    '''

    l_1 = range(begin, end)  # range是内置函数，begin开始，（end-1）结束
    l_end = []
    for i in l_1:
        if i > num1:
            l_end.append(i)
    return l_end


def id2p(i_d, orders_f):
    '''
    7天的是orders_f， 13周的是data_orders
    取id对应的物料编码
    :param i_d:
    :return:
    '''
    return orders_f[orders_f['id'] == i_d]['package'].values[0]


# TODO 这个地方 t 和 f 应该都是可选参数，需要处理
def type_weight(m, n, k, s_t, o_t, wei, type, f=0):
    '''
    将不同类型的优先级使用1，2，3分别表示delay，lose，holding
    :param m:
    :param n:
    :param k:
    :param s_t:
    :param o_t:
    :param t:
    :param type:
    :return:
    '''
    if type == 1:
        return f * 1000 + 700 / o_t + 70 / s_t + weight(wei, m, n)
    elif type == 2:
        return f * 100 + 70 / o_t + 7 / s_t + weight(wei, m, n)


def get_sample(data_orders, BOM, flag):
    unique_package_bom = pd.DataFrame(data_orders, columns=['package', 'bom'])
    unique_package_bom.drop_duplicates(subset=['package', 'bom'], keep='first', inplace=True)
    unique_package_bom.reset_index(drop=True, inplace=True)
    if flag == 7:
        unique_package_bom.rename(columns={'package': 'pack'}, inplace=True)
        df_merge_pack = pd.merge(unique_package_bom, BOM, on=['pack'])
        sample_data = df_merge_pack['sample']
    elif flag == 13:
        unique_package_bom.rename(columns={'package': 'pack'}, inplace=True)
        df_merge_pack = pd.merge(unique_package_bom, BOM, on=['pack'])
        sample_data = df_merge_pack['sample']
    return sample_data


def packing_t(t, T_COVER, T):
    if t > T_COVER:
        if t - 2 > T_COVER:
            return range(t - 2, T[-1] + 1)
        else:
            return range(T_COVER + 1, T[-1] + 1)
    elif t - 2 <= 0:
        return range(1, T[-1] + 1)
    else:
        return range(t - 2, T[-1] + 1)


def get_xindex_x1index(order_id, orders_f, pack_range, flag, fix_num):
    # TODO 重构,这个copy要好好看一下
    xindex = {}
    x1index = {}
    if flag == 7:
        for i_d in order_id:
            xindex[i_d] = []
            x1index[i_d] = []
            index_m = {}
            sub_df = orders_f[orders_f['id'] == i_d]
            sub_df = sub_df.reset_index(drop=True)
            sub_df.rename(columns={'package': 'm', 'warehouse': 'k'}, inplace=True)  # 重命名
            sub_series = sub_df.loc[0, ['id', 'm', 'n', 'k', 's_t', 'o_t']]  # 取第一行，自适应转成Series
            index_m = sub_series.to_dict()  # Series转字典类型
            index_x1 = index_m.copy()
            x1index[i_d].append(index_x1)
            print('sub_df: \n {0} \n Type: {1} \n index_m: \n {2}'.format(sub_series, type(sub_series), index_m))
            if sub_df.loc[0, 'isLock'] == 1:
                index_m['t'] = sub_df.loc[0, 'o_t']
                index_mm = index_m.copy()
                xindex[i_d].append(index_mm)
            else:
                for p_t in range(fix_num + 1, pack_range[-1] + 1):
                    index_m['t'] = p_t
                    index_mm = index_m.copy()
                    xindex[i_d].append(index_mm)
        print('index_m:\n {0},\n x1index: \n {1}, \n xindex: \n {2}'.format(index_m, x1index.keys(), xindex.values()))
    elif flag == 14:
        for i_d in order_id:
            xindex[i_d] = []
            x1index[i_d] = []
            index_m = {}
            sub_df = orders_f[orders_f['id'] == i_d]
            sub_df = sub_df.reset_index(drop=True)
            sub_df.rename(columns={'package': 'm', 'warehouse': 'k', 'flag': 'f'}, inplace=True)  # 重命名
            sub_series = sub_df.loc[0, ['id', 'm', 'n', 'k', 's_t', 'o_t', 'f']]  # 取第一行，自适应转成Series
            index_m = sub_series.to_dict()  # Series转字典类型
            index_x1 = index_m.copy()  # 这个地方为什么要copy
            x1index[i_d].append(index_x1)
            print('sub_df: \n {0} \n Type: {1} \n index_m: \n {2}'.format(sub_series, type(sub_series), index_m))
            for p_t in packing_t(index_m['o_t'], fix_num, pack_range):
                index_m['t'] = p_t
                index_mm = index_m.copy()
                xindex[i_d].append(index_mm)
    return xindex, x1index


def get_yindex(iterIndex, p_id, data_orders, PackSample):
    x_index = copy.deepcopy(iterIndex)
    y_index = {}
    for i_d in p_id:
        y_index[i_d] = []
        sample = PackSample[data_orders[data_orders['id'] == i_d]['package'].values[0]]
        for i in x_index[i_d]:
            for s in sample:
                i['s'] = s
                i_y = i.copy()
                y_index[i_d].append(i_y)
    return y_index


def get_package_sample(BOM, package):
    PackSample = {}
    for p in package:
        PackSample[p] = BOM[BOM['pack'] == p]['sample'].unique()
    return PackSample


def create_x_tupledict(p_id, iterIndex, solver, infinity, flag):
    x = tupledict()  # tupledict类是基于Python字典类的封装
    print('i_d in p_id: \n {0} \n iterIndex: \n {1}'.format(p_id, iterIndex))
    if flag == 7:
        for i_d in p_id:
            for i in iterIndex[i_d]:
                x[i['id'], i['m'], i['n'], i['k'], i['s_t'], i['o_t'], i['t']] \
                    = solver.IntVar(0.0, infinity, name='x{}{}'.format(i['id'], i['t']))
    elif flag == 14:
        for i_d in p_id:
            for i in iterIndex[i_d]:
                x[i['id'], i['m'], i['n'], i['k'], i['s_t'], i['o_t'], i['f'], i['t']] \
                    = solver.IntVar(0.0, infinity, name='x{}{}'.format(i['id'], i['t']))
    print('Number of variables ={}'.format(solver.NumVariables()))
    # tupledict的key（键）在内部的存储格式是tuplelist
    print('x variables ={}'.format(x))
    return x


def create_y_tupledict(p_id, yIndex, solver, infinity):
    y = tupledict()
    for i_d in p_id:
        for i in yIndex[i_d]:
            y[i['s'], i['id'], i['m'], i['n'], i['k'], i['s_t'], i['o_t'], i['f'], i['t']] \
                = solver.IntVar(0.0, infinity, name='y{}{}{}'.format(i['s'], i['id'], i['t']))
    print('Number of variables ={}'.format(solver.NumVariables()))
    # tupledict的key（键）在内部的存储格式是 tuplelist
    print('y variables ={}'.format(y))
    return y


def create_invent_tupledict(warehouse, sample, pack_range, solver, up_bound):
    invent = tupledict()
    # itertools.product 求笛卡尔积
    for k, s, t in itertools.product(warehouse, sample, pack_range):
        invent[k, s, t] = solver.NumVar(0.0, up_bound, name='I{}{}{}'.format(k, s, t))
    print('Number of variables invent =', solver.NumVariables())
    print('Invent variables ={}'.format(invent))
    return invent


def create_x_1_tupledict(p_id, x1Index, solver, infinity, flag):
    x_1 = tupledict()
    if flag == 7:
        for i_d in p_id:
            for i in x1Index[i_d]:
                x_1[i['id'], i['m'], i['n'], i['k'], i['s_t'], i['o_t']] \
                    = solver.IntVar(0.0, infinity, name='x_1{}'.format(i['id']))
    elif flag == 14:
        for i_d in p_id:
            for i in x1Index[i_d]:
                x_1[i['id'], i['m'], i['n'], i['k'], i['s_t'], i['o_t'], i['f']] \
                    = solver.IntVar(0.0, infinity, name='x_1{}'.format(i['id']))
    print('Number of variables x_1 =', solver.NumVariables())
    print('x_1 variables ={}'.format(x_1))
    return x_1


def create_x_2_tupledict(p_id, iterIndex, solver, infinity, flag):
    x_2 = tupledict()
    if flag == 7:
        for i_d in p_id:
            for i in iterIndex[i_d]:
                if i['t'] >= i['o_t']:
                    x_2[i['id'], i['m'], i['n'], i['k'], i['s_t'], i['o_t'], i['t']] \
                        = solver.IntVar(0.0, infinity, name='x_2{}{}'.format(i['id'], i['t']))
    elif flag == 14:
        for i_d in p_id:
            for i in iterIndex[i_d]:
                if i['t'] >= i['o_t']:
                    x_2[i['id'], i['m'], i['n'], i['k'], i['s_t'], i['o_t'], i['f'], i['t']] \
                        = solver.IntVar(0.0, infinity, name='x_2{}{}'.format(i['id'], i['t']))

    print('Number of variables x_2 =', solver.NumVariables())
    print('x_2 variables ={0}\n type: {1}'.format(x_2, type(x_2)))
    return x_2

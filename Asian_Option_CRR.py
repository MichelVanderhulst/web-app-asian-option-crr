import networkx as nx
from scipy.stats import norm
import numpy as np

#######################################################################################################################
### Asian Option
### CRR model
### Geometric Random Walk
###
### SOURCES:
# Stochastic Calculus for Finance I The Binomial Asset Pricing Model (Springer Finance) by Steven E. Shreve -> for the model. Slightly modifed.
#
#  Yuxing Yan Python for Finance 2nd edition -> the script for the binomial tree. Modified for Asian options.
#######################################################################################################################

def RepStrat_Asian_Option_CRR(CallOrPut, S, K, rf, T, mu, vol, tree__periods):

####################################################################################################################
    #####################  START derivative/model specifics, user input transformation             #####################

    if CallOrPut == "Call":
        phi = 1
    elif CallOrPut == "Put":
        phi = -1

    #####################  START derivative/model specifics, user input transformation             #####################
    ####################################################################################################################


    ####################################################################################################################
    #####################                  START accounts initialization                           #####################

    G_Stock, G_Intrinsic, G_Price, G_Portfolio, G_CashAccount, G_Shares = nx.Graph(), nx.Graph(), nx.Graph(), nx.Graph(), nx.Graph(), nx.Graph()

    stockprices, sumstockprices, optionintrinsicvalue, optionprice, CashAccount, NbrOfShares, Portfolio = {}, {}, {}, {}, {}, {}, {}

    #####################                      END accounts initialization                         #####################
    ####################################################################################################################

    ####################################################################################################################
    #####################                  START replication strategy                              #####################
    #### dt, up factor, down factor, discounting factor, probUpFactor, probDownFact

    step = T / tree__periods
    u = np.exp(mu * step + vol * np.sqrt(step))
    d = np.exp(mu * step - vol * np.sqrt(step))

    discFact = np.exp(-rf * step)

    probUp = (np.exp(rf * step) - d) / (u - d)
    probDown = 1 - probUp

    stockprices[(0, 1)] = S
    sumstockprices[(0, 1)] = S
    stockprices[(1, 1)] = S*u
    sumstockprices[(1, 1)] = S*u
    stockprices[(1, 2)] = S*d
    sumstockprices[(1, 2)] = S*d

    # Create the edges, compute the stock price and option intrinsic value at all nodes
    for i in range(0, tree__periods + 1):
        counter = 0
        for j in range(1, (2 ** i) + 1):
            if i < tree__periods:
                # CREATION OF THE EDGES
                G_Stock.add_edge((i, j), (i + 1, j + counter))
                G_Stock.add_edge((i, j), (i + 1, j + 1 + counter))

                G_Intrinsic.add_edge((i, j), (i + 1, j + counter))
                G_Intrinsic.add_edge((i, j), (i + 1, j + 1 + counter))

                G_Price.add_edge((i, j), (i + 1, j + counter))
                G_Price.add_edge((i, j), (i + 1, j + 1 + counter))

                G_Portfolio.add_edge((i, j), (i + 1, j + counter))
                G_Portfolio.add_edge((i, j), (i + 1, j + 1 + counter))

                G_CashAccount.add_edge((i, j), (i + 1, j + counter))
                G_CashAccount.add_edge((i, j), (i + 1, j + 1 + counter))

                G_Shares.add_edge((i, j), (i + 1, j + counter))
                G_Shares.add_edge((i, j), (i + 1, j + 1 + counter))

                # stock price and option intrinsic value at all nodes
                stockprices[(i, j)] = stockprices[(i, j)]
                stockprices[(i + 1, j + counter)] = stockprices[(i, j)] * u
                stockprices[(i + 1, j + 1 + counter)] = stockprices[(i, j)] * d

                sumstockprices[(i, j)] = sumstockprices[(i, j)]
                sumstockprices[(i + 1, j + counter)] = stockprices[(i, j)] * u + sumstockprices[(i, j)]
                sumstockprices[(i + 1, j + 1 + counter)] = stockprices[(i, j)] * d + sumstockprices[(i, j)]

                optionintrinsicvalue[(i, j)] =max(phi * (((1 / (i + 2)) * sumstockprices[(i, j)]) - K), 0)  
                optionintrinsicvalue[(i + 1, j + counter)] = max(phi * (((1 / (i + 2)) * sumstockprices[(i + 1, j + counter)]) - K), 0)
                optionintrinsicvalue[(i + 1, j + 1 + counter)] =  max(phi * (((1 / (i + 2)) * sumstockprices[(i + 1, j + 1 + counter)]) - K), 0)

                counter += 1

    # option price at all nodes
    counter = 0
    for i in range(tree__periods, -1, -1):
        counter = 0
        for j in range(1, (2 ** i) + 1):
            # values at maturity are not discounted given we start there
            if i == tree__periods:
                optionprice[(i, j)] = optionintrinsicvalue[(i, j)]

            # all the others, until price at t=0
            else:
                optionprice[(i, j)] = discFact * (probUp * optionprice[(i + 1, j + counter)] + probDown * optionprice[(i + 1, j + 1 + counter)])

            counter += 1

    Portfolio[(0, 1)] = optionprice[(0, 1)]

    # changer l'algo qui tourne autour des nodes, car trop lent avec les nodes.
    for i in range(0, tree__periods + 1):
        counter = 0
        for j in range(1, (2**i) +1):
            if i < tree__periods:
                # initialize / After Rebalancing
                NbrOfShares[(i, j)] = (optionprice[(i + 1, j+counter)] - optionprice[(i + 1, j + 1+counter)]) / (  (u-d)*stockprices[(i,j)]  )
                CashAccount[(i, j)] = Portfolio[(i, j)] - NbrOfShares[(i, j)] * stockprices[(i, j)]

                # Before Rebalancing
                NbrOfShares[(i + 1, j+counter)] = NbrOfShares[(i, j)]
                CashAccount[(i + 1, j+counter)] = CashAccount[(i, j)] * np.exp(rf * step)
                Portfolio[(i + 1, j+counter)] = CashAccount[(i + 1, j+counter)] + NbrOfShares[(i + 1, j+counter)] * stockprices[(i + 1, j+counter)]

                NbrOfShares[(i + 1, j + 1+counter)] = NbrOfShares[(i, j)]
                CashAccount[(i + 1, j + 1+counter)] = CashAccount[(i, j)] * np.exp(rf * step)
                Portfolio[(i + 1, j + 1+counter)] = CashAccount[(i + 1, j + 1+counter)] + NbrOfShares[(i + 1, j + 1+counter)] * stockprices[(i + 1, j + 1+counter)]

                counter += 1

            elif i == tree__periods:
                CashAccount[(i, j)] = CashAccount[(i, j)] + NbrOfShares[(i, j)] * stockprices[(i, j)]
                NbrOfShares[(i, j)] = 0

    # creating the nodes itself in the networkx graph
    pos = {}
    count = tree__periods
    for node in G_Stock.nodes():
        pos[node] = (node[0], tree__periods + 2 + node[0] - (2 + count) * node[1])
        count += 1

    edge_x = []
    edge_y = []
    node_x = []
    node_y = []
    stocksLabel = []
    optionpriceLabel = []
    portfolioLabel = []
    cashLabel = []
    nbrofsharesLabel = []
    SumStockPricesLabel = []

    for edge in G_Stock.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)


    for node in pos:
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        stocksLabel.append(round(stockprices[node],2))
        SumStockPricesLabel.append(round(sumstockprices[node],2))
        optionpriceLabel.append(round(optionprice[node],2))
        portfolioLabel.append(round(Portfolio[node],2))
        cashLabel.append(round(CashAccount[node],2))
        nbrofsharesLabel.append(round(NbrOfShares[node],2))
                                                                                                   
    return nbrofsharesLabel, cashLabel, portfolioLabel, optionpriceLabel, SumStockPricesLabel, stocksLabel, edge_x, edge_y, node_x, node_y, round(u,2), round(d,2), round(probUp,2), round(probDown,2)


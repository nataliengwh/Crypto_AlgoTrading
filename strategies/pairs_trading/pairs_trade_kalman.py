from strategies.base import StrategyBase
from pykalman import KalmanFilter
import pandas as pd
import numpy as np
import math

import logging
_logger = logging.getLogger(__name__)


class PairsTradeKalman(StrategyBase):

    params = dict(
        lookback=20,
        enter_std=2,
        exit_std=1,  # 0.5
        stop_loss=-0.01,  # -0.015
        coin0='',
        coin1='',
        )

    ##################################### INIT #####################################

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using Pairs Trading strategy")
        # parameter
        self.lookback = self.p.lookback
        self.enter_std = self.p.enter_std
        self.exit_std = self.p.exit_std
        self.stop_loss = self.p.stop_loss
        self.coin0 = self.p.coin0
        self.coin1 = self.p.coin1
        # trading variable
        self.status = "no_position"
        self.spread = 0
        self.qty0, self.qty1 = 0, 0
        self.ts = None
        # threshold for enter and exit
        self.enter_upper, self.enter_lower = None, None
        self.exit_upper, self.exit_lower = None, None
        # for kalman filter
        self.alpha, self.intercept = 0, 0
        self.spread_std = 0
        # tracking PNL
        self.start_cash = 0
        self.long_coin0_PL, self.long_coin0_count = 0, 0
        self.short_coin0_PL, self.short_coin0_count = 0, 0
        self.stop_loss_PL, self.stop_loss_count = 0, 0

    def _calculate_current_position(self) -> float:
        coin0_value = self.qty0 * self.data0[0]
        coin1_value = self.qty1 * self.data1[0]
        if self.status == 'long_coin0':
            return + coin0_value - coin1_value
        elif self.status == 'short_coin0':
            return - coin0_value + coin1_value

    def _calculate_starting_position(self) -> None:
        coin0_value = self.qty0 * self.data0[0]
        coin1_value = self.qty1 * self.data1[0]
        self.start_pos = self._calculate_current_position()
        self.start_cash = + coin0_value + coin1_value

    def _get_param_from_kalman_filter(self) -> None:
        Y = np.log(pd.Series(self.data0.get(size=self.lookback, ago=0), dtype='float64').values)[:, np.newaxis]
        X = np.log(pd.Series(self.data1.get(size=self.lookback, ago=0), dtype='float64').values)[:, np.newaxis]

        # observation matrix
        C = np.hstack((np.ones_like(X), X))
        C = C.reshape(self.lookback, 1, 2)

        # state transition matrix
        I = np.array([[[1, 0],
                       [0, 1]]])
        T = I.repeat(self.lookback - 1, axis=0)

        self.kf = KalmanFilter(em_vars=['transition_covariance',
                                        'observation_covariance',
                                        'initial_state_mean',
                                        'initial_state_covariance'],
                               transition_matrices=T,
                               observation_matrices=C,
                               n_dim_state=2,
                               n_dim_obs=1)

        # run EM algorithm
        self.kf.em(X=Y, n_iter=10)
        self.spread_std = math.sqrt(self.kf.observation_covariance[0][0])

        # filtering
        filtered_state_means, filtered_state_covariances = self.kf.filter(X=Y)
        self.filtered_state_means, self.filtered_state_covariances = filtered_state_means[-1], \
                                                                     filtered_state_covariances[-1]
        self.alpha, self.intercept = self.filtered_state_means[1], self.filtered_state_means[0]

    def get_threshold(self):
        try:  # for unaligned time
            self._get_param_from_kalman_filter()
            # update entry and exit levels
            self.enter_upper = self.enter_std * self.spread_std
            self.exit_upper = self.exit_std * self.spread_std
            self.enter_lower = -1 * self.enter_std * self.spread_std
            self.exit_lower = -1 * self.exit_std * self.spread_std

            if self.spread > self.enter_upper and self.alpha > 0:
                # indicates that cn0 is overpriced
                self.short_coin0()
            elif self.spread < self.enter_lower and self.alpha > 0:
                # indicates that cn1 is overpriced
                self.long_coin0()
        except:
            pass

    def long_coin0(self):
        self.status = 'long_coin0'
        self.qty0 = round(self.broker.getvalue() / 2 / self.data0[0], 2) # round FOR BTC
        self.qty1 = int(self.broker.getvalue() / 2 / self.data1[0])
        self.buy(data=self.data0,size=self.qty0)
        self.sell(data=self.data1, size=self.qty1)
        print(f"###### [{self.ts}] ###### Long {self.coin0} ######")
        print(f"Long {self.qty0} {self.coin0} @ {self.data0[0]}")
        print(f"Short {self.qty1} {self.coin1} @ {self.data1[0]}")
        self._calculate_starting_position()


    def short_coin0(self):
        self.status = 'short_coin0'
        self.qty0 = round(self.broker.getvalue() / 2 / self.data0[0],2)
        self.qty1 = int(self.broker.getvalue() / 2 / self.data1[0])
        self.sell(data=self.data0, size=(self.qty0))
        self.buy(data=self.data1, size=(self.qty1))
        print(f"###### [{self.ts}] ###### Short {self.coin0} ######")
        print(f"Short {self.qty0} {self.coin0} @ {self.data0[0]}")
        print(f"Long {self.qty1} {self.coin1} @ {self.data1[0]}")
        self.start_pos = -(self.qty0 * self.data0[0])+(self.qty1 * self.data1[0])
        self._calculate_starting_position()

    def exit_trade(self, case):
        self.status = 'no_position'
        print(f"[{self.ts}] PNL {self.trade_pnl:.1f}, {self.trade_pnl_pct:.4f}%")
        print(f"exit @ {self.data0[0]}, {self.data1[0]}")
        # track PNL for different cases
        if case == 1:
            self.long_coin0_PL += self.trade_pnl
            self.long_coin0_count += 1
        elif case == 2:
            self.short_coin0_PL += self.trade_pnl
            self.short_coin0_count += 1
        else:  # case = 3 for stop loss
            self.stop_loss_PL += self.trade_pnl
            self.stop_loss_count += 1
        self.close(self.data0)
        self.close(self.data1)
        # initialize tracker for new trade
        self.qty0, self.qty1 = 0, 0
        self.start_pos, self.start_cash = 0, 0
        self.trade_pnl, self.trade_pnl_pct = 0, 0


    def check_exit_condition(self) -> None:
        current_pos = self._calculate_current_position()
        self.trade_pnl = current_pos - self.start_pos
        self.trade_pnl_pct = self.trade_pnl / self.start_cash
        if self.status == 'long_coin0':
            if self.spread > self.exit_lower:
                self.exit_trade(case=1)
            elif self.trade_pnl_pct < self.stop_loss:
                self.exit_trade(case=3)
        elif self.status == 'short_coin0':
            if self.spread < self.exit_upper:
                self.exit_trade(case=2)
            elif self.trade_pnl_pct < self.stop_loss:
                self.exit_trade(case=3)

    ##################################### EXECUTE #####################################

    def next(self):
        self.spread = (math.log(self.data0[0]) - self.alpha * math.log(self.data1[0]) - self.intercept)
        self.ts = self.data0.datetime.datetime().strftime("%d-%m-%y %H:%M")
        if self.status == 'no_position':
            self.get_threshold()
        else:
            self.check_exit_condition()

    def stop(self):
        print("##################### BACKTEST COMPLETED #####################")
        print(f"Final Portfolio: {self.broker.getvalue():.1f}, Return: {((self.broker.getvalue()/1000000)-1)*100:.1f}%")
        print(f"Lookback: {self.lookback}, Enter SD: {self.enter_std},")
        print(f"Exit SD: {self.exit_std}, Stop Loss: {self.stop_loss},")
        print(f"Cumulative PL from Long {self.coin0} is {self.long_coin0_PL:.1f} from {self.long_coin0_count} trades")
        print(f"Cumulative PL from Short {self.coin0} is {self.short_coin0_PL:.1f} from {self.short_coin0_count} trades")
        print(f"Cumulative PL from Stop Loss is {self.stop_loss_PL:.1f} from {self.stop_loss_count} trades")
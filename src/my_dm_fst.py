from __future__ import annotations


#
# 有限オートマトンによる対話管理を行うクラス
#
class DmFst:

    # 現在の状態番号
    current_state = -1

    # 初期状態
    start_state = -1

    # 遷移条件にマッチしたユーザ発話を保持する
    context_user_utterance = []

    # 終了状態に達したかどうか
    end = False

    # 初期化
    def __init__(self, recipe: dict[int, str]):
        self.recipe = recipe
        self.def_fst()
        self.reset()
        self.end = False

    # 有限オートマトンを定義
    def def_fst(self):

        # 状態の定義

        ## 状態番号、対応するシステム発話
        num_recipe = len(self.recipe)

        self.start_state = 0
        self.recipe_start_state = 1
        self.recipe_last_state = num_recipe
        self.end_state = num_recipe + 1
        self.too_prev_state = num_recipe + 2
        self.too_forward_state = num_recipe + 3
        self.over_number = num_recipe + 4
        self.unknown = num_recipe + 5
        states = {
            self.start_state: "レシピ読み上げさんです．レシピ写真をアップロードしてください．",
            self.end_state: "上手に作れましたか？読み上げを終了します．",
            self.too_forward_state: "手順はこれ以上ありません．",
            self.too_prev_state: "前の手順はありません．",
            self.over_number: "その番号の手順はありません．",
            self.unknown: "すみません，もう一度おっしゃってください.",
        }
        self.states = {**self.recipe, **states}

    # 入力であるユーザ発話に応じてシステム発話を出力し、内部状態を遷移させる
    # ただし、ユーザ発話の情報は「意図、フレーム名、フレーム値」のlistとする
    def enter(self, user_utterance):

        system_utterance = ""

        # フレーム名に対して行う
        # 最初の0番目のindexは1発話に対して複数のスロットが抽出された場合に対応するため
        # ここでは1発話につき１つのフレームしか含まれないという前提
        slot_name = user_utterance["slot_name"]
        slot_value = user_utterance["slot_value"]

        # from_top = "(最初から|初めから|始めから|一から|1から|最初に戻)"
        # first_proc = "(最初|初め|始め|まず)"
        # next_proc = "次"
        # repeat = "(もう1度|もう一度|再度|もう1回|もう一回|もっかい|なんて|何て)"  # proc_noよりもこちらを優先的に見るようにする(中に"1"というのが両方に含まれているから)
        # prev_proc = "(前|戻)"
        # proc_no = "(" + "|".join([f"{i}つ目|{i}番" for i in range(1, self.num_proc)]) + ")"
        # end = "(終わり|おわり|終了|もういいよ)"

        # self.frames = [
        #     ["from the top", from_top],
        #     ["first procedure", first_proc],
        #     ["next procedure", next_proc],
        #     ["repeat", repeat],
        #     ["previous procedure", prev_proc],
        #     ["No. of procedure", proc_no],
        #     ["end", end],
        # ]

        if slot_name == "from the top" or slot_name == "first procedure":
            self.current_state = self.recipe_start_state
            system_utterance = self.get_system_utterance()
        elif slot_name == "next procedure":
            if self.start_state <= self.current_state < self.recipe_last_state:
                self.current_state += 1
                system_utterance = self.get_system_utterance()
            elif self.current_state == self.recipe_last_state:  # 現在がレシピの最後の状態
                self.current_state = self.too_forward_state
                system_utterance = self.get_system_utterance()
                self.current_state = self.recipe_last_state
        elif slot_name == "repeat":
            system_utterance = self.get_system_utterance()
        elif slot_name == "previous procedure":
            if self.recipe_start_state < self.current_state <= self.recipe_last_state:
                self.current_state -= 1
                system_utterance = self.get_system_utterance()
            elif self.current_state == self.recipe_start_state:
                self.current_state = self.too_prev_state
                system_utterance = self.get_system_utterance()
                self.current_state = self.recipe_start_state
        elif slot_name == "No. of procedure":
            tmp = self.current_state
            slot_value = int(slot_value[0])
            if self.recipe_start_state <= slot_value <= self.recipe_last_state:
                self.current_state = slot_value
                system_utterance = self.get_system_utterance()
            else:
                self.current_state = self.over_number
                system_utterance = self.get_system_utterance()
            self.current_state = tmp
        elif slot_name == "unknown":
            tmp = self.current_state
            self.current_state = self.unknown
            system_utterance = self.get_system_utterance()
            self.current_state = tmp
        elif slot_name == "end":
            self.current_state = self.end_state
            system_utterance = self.get_system_utterance()
            self.end = True
        return system_utterance

    # 初期状態にリセットする
    def reset(self):
        self.current_state = self.start_state
        self.end = False

    # 指定された状態に対応するシステムの発話を取得
    def get_system_utterance(self):
        # utterance = ""
        # for state_ in self.states:
        # if self.current_state == state_[0]:
        # utterance = state_[1]
        return self.states[self.current_state]


if __name__ == "__main__":

    dm = DmFst()

    # 初期状態の発話を表示
    print("システム発話 : " + dm.get_system_utterance())

    # ユーザ発話を設定
    user_utterance = [{"slot_name": "place", "slot_value": "京都駅周辺"}]
    print("ユーザ発話")
    print(user_utterance)
    print()

    # 次のシステム発話を表示
    print("システム発話")
    print(dm.enter(user_utterance))

    # 誤った発話を入力してみる

    # ユーザ発話を設定
    user_utterance = [{"slot_name": "place", "slot_value": "新宿"}]
    print("ユーザ発話")
    print(user_utterance)
    print()

    # 次のシステム発話を表示
    print("システム発話")
    print(dm.enter(user_utterance))

    # ユーザ発話を設定
    user_utterance = [{"slot_name": "genre", "slot_value": "和食"}]
    print("ユーザ発話")
    print(user_utterance)
    print()

    # 次のシステム発話を表示
    print("システム発話")
    print(dm.enter(user_utterance))

    # ユーザ発話を設定
    user_utterance = [{"slot_name": "budget", "slot_value": "3000円以下"}]
    print("ユーザ発話")
    print(user_utterance)
    print()

    # 次のシステム発話を表示
    print("システム発話")
    print(dm.enter(user_utterance))

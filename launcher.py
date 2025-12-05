import os
import json
import subprocess
import random
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from collections import defaultdict
import hashlib


#класс жанров, ДОБАВЬ БОЛЬШЕ!!!!
class GameGenre:
    ACTION = "Экшен"
    RPG = "RPG"
    STRATEGY = "Стратегия"
    SIMULATION = "Симулятор"
    ADVENTURE = "Приключения"
    SPORTS = "Спорт"
    RACING = "Гонки"
    SHOOTER = "Шутер"
    HORROR = "Хоррор"
    ALL = [ACTION, RPG, STRATEGY, SIMULATION, ADVENTURE, SPORTS, RACING, SHOOTER, HORROR]

class Game:
    def __init__(self, name, path, arguments="", genres=None):
        self.name = name
        self.path = path
        self.arguments = arguments #аргументы запуска вырезать я хз че с ними делать и как
        self.genres = set(genres) if genres else set()
        self.play_count = 0
        self.total_time = 0
        self.last_played = None
        self.rating = 0.0
        self.game_id = hashlib.md5(f"{name}_{path}".encode()).hexdigest()
    def play(self):
        self.play_count += 1
        self.last_played = datetime.now() #оно не работает!!!
        self.total_time += 60
    def set_rating(self, rating):
        self.rating = max(1.0, min(5.0, rating))
    def launch(self):
        try:
            if not os.path.exists(self.path):
                return False

            self.play()

            cmd = [self.path]
            #if self.arguments:
           #     cmd.extend(self.arguments.split())

            subprocess.Popen(cmd, cwd=os.path.dirname(self.path))
            return True
        except:
            return False
#список игр забыл описание добавить потом уже
    def to_dict(self):
        return {
            "name": self.name,
            "path": self.path,
            "arguments": self.arguments,
            "genres": list(self.genres),
            "play_count": self.play_count,
            "total_time": self.total_time,
            # "last_played": self.last_played.isoformat() if self.last_played else None,
            "rating": self.rating,
            "game_id": self.game_id
        }

    @classmethod
    def from_dict(cls, data):
        game = cls(
            name=data["name"],
            path=data["path"],
            arguments=data.get("arguments", ""),
            genres=data.get("genres", [])
        )

        game.play_count = data.get("play_count", 0)
        game.total_time = data.get("total_time", 0)
        #if data.get("last_played"):
        #    game.last_played = datetime.fromisoformat(data["last_played"])
        game.rating = data.get("rating", 0.0)
        game.game_id = data.get("game_id", game.game_id)

        return game


class GameRecommender:
    def __init__(self):
        pass

    def get_features(self, game):
        features = []

        for genre in GameGenre.ALL:
            features.append(1 if genre in game.genres else 0)
        features.append(min(game.total_time / 1000, 1.0))
        features.append((game.rating - 1) / 4)
        return np.array(features)

    def recommend(self, user_games, all_games, count=3):
        if not user_games or not all_games:
            return []

        user_ids = {g.game_id for g in user_games}
        available = [g for g in all_games if g.game_id not in user_ids]
        if not available:
            return []

        if len(user_games) == 0:
            return random.sample(available, min(count, len(available)))
        user_profile = np.mean([self.get_features(g) for g in user_games], axis=0)
        scores = []
        for game in available:
            game_features = self.get_features(game)

            if np.all(game_features == 0) or np.all(user_profile == 0):
                similarity = 0.0
            else:
                similarity = np.dot(user_profile, game_features)
                norm = np.linalg.norm(user_profile) * np.linalg.norm(game_features)
                if norm > 0:
                    similarity /= norm
            scores.append((game, similarity))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [g for g, _ in scores[:count]]


class GameLibrary:
    def __init__(self, save_file="games.json"):
        self.save_file = save_file
        self.games = {}
        self.recommender = GameRecommender()
        self.load()

    def add(self, game):
        self.games[game.game_id] = game
        self.save()

    def remove(self, game_id):
        if game_id in self.games:
            del self.games[game_id]
            self.save()
            return True
        return False

    def get_all(self):
        return list(self.games.values())

    def get_recommendations(self, count=3):
        all_games = self.get_all()
        return self.recommender.recommend(all_games, all_games, count)

    def save(self):
        try:
            data = {"games": {gid: g.to_dict() for gid, g in self.games.items()}}
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass

    def load(self):
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.games.clear()
                for gid, gdata in data.get("games", {}).items():
                    try:
                        game = Game.from_dict(gdata)
                        self.games[gid] = game
                    except:
                        continue
        except:
            pass


class GameLauncherApp:
    def __init__(self):
        self.library = GameLibrary()
        self.setup_window()

    def setup_window(self):
        self.window = tk.Tk()
        self.window.title("ManageLauncher")
        self.window.geometry("500x550")
        style = ttk.Style()
        style.theme_use('classic')
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.setup_games_tab()
        self.setup_recommend_tab()
        self.update_list()

    def setup_games_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Библиотека")
        ttk.Label(tab, text="Моя библиотека", font=('Arial', 20)).pack(pady=10)
        frame = ttk.Frame(tab)
        frame.pack(fill=tk.BOTH, expand=True, padx=20)
        list_frame = ttk.LabelFrame(frame, text="Cписок игр", padding=15)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.game_list = tk.Listbox(list_frame, height=15, font=('Arial', 10))
        self.game_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.game_list.config(yscrollcommand=scroll.set)
        scroll.config(command=self.game_list.yview)
        self.game_list.bind('<Double-Button-1>', self.launch_game)
        self.game_list.bind('<<ListboxSelect>>', self.select_game)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side=tk.RIGHT, padx=20)
        ttk.Button(btn_frame, text="Запустить", command=self.launch_game, width=15).pack(pady=5)
        ttk.Button(btn_frame, text="Добавить", command=self.add_game, width=15).pack(pady=5)
        ttk.Button(btn_frame, text="Удалить", command=self.remove_game, width=15).pack(pady=5)
        ttk.Button(btn_frame, text="Оценить", command=self.rate_game, width=15).pack(pady=5)
        info_frame = ttk.LabelFrame(tab, text="Информация", padding=10)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        self.name_label = ttk.Label(info_frame, text="Название: не выбрано")
        self.name_label.pack(anchor=tk.W)
        self.genre_label = ttk.Label(info_frame, text="Жанры: не выбрано")
        self.genre_label.pack(anchor=tk.W)
        self.stats_label = ttk.Label(info_frame, text="Запусков: 0 | Рейтинг: 0.0")
        self.stats_label.pack(anchor=tk.W)

    def setup_recommend_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Рекомендации")
        ttk.Label(tab, text="Рекомендации", font=('Arial', 20)).pack(pady=10)
        ttk.Button(tab, text="Показать рекомендации", command=self.show_recommendations, width=50).pack(pady=10)
        self.rec_text = tk.Text(tab, height=15, wrap=tk.WORD, font=('Arial', 10))
        self.rec_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        scroll = ttk.Scrollbar(tab)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.rec_text.config(yscrollcommand=scroll.set)
        scroll.config(command=self.rec_text.yview)
        ttk.Button(tab, text="Запустить случайную игру", command=self.launch_random,width=50).pack(pady=10)

    def update_list(self):
        self.game_list.delete(0, tk.END)
        for game in self.library.get_all():
            self.game_list.insert(tk.END, f"{game.name} ({game.rating:.1f})")

    def select_game(self, event=None):
        selection = self.game_list.curselection()
        if not selection:
            return
        index = selection[0]
        name_with_rating = self.game_list.get(index)
        game_name = name_with_rating.split(" (")[0]
        for game in self.library.get_all():
            if game.name == game_name:
                self.name_label.config(text=f"Название: {game.name}")
                genres = ", ".join(game.genres) if game.genres else "не указаны"
                self.genre_label.config(text=f"Жанры: {genres}")
                self.stats_label.config(text=f"Запусков: {game.play_count} | Рейтинг: {game.rating:.1f}")
                break
    def add_game(self):
        path = filedialog.askopenfilename(
            title="Выберите файл игры",
            filetypes=[("Игры", "*.exe"), ("бубубубуфууубууу", "*.*")]
        )
        if not path:
            return

        name = simpledialog.askstring("Название", "Введите название игры:",initialvalue=os.path.splitext(os.path.basename(path))[0])
        if not name:
            return


        genre_win = tk.Toplevel(self.window)
        genre_win.title("Выберите жанры")
        genre_win.geometry("250x300")
        selected = []
        vars_dict = {}
        ttk.Label(genre_win, text="Жанры игры:").pack(pady=10)
        for genre in GameGenre.ALL:
            var = tk.BooleanVar()
            vars_dict[genre] = var
            ttk.Checkbutton(genre_win, text=genre, variable=var).pack(anchor=tk.W, padx=20)

        def save():
            selected.clear()
            for genre, var in vars_dict.items():
                if var.get():
                    selected.append(genre)
            genre_win.destroy()
        ttk.Button(genre_win, text="Готово", command=save).pack(pady=20)
        self.window.wait_window(genre_win)
        game = Game(name=name, path=path, genres=selected)
        self.library.add(game)
        self.update_list()
        messagebox.showinfo("Готово", f"Игра '{name}' добавлена")

    def remove_game(self):
        selection = self.game_list.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите игру")
            return
        index = selection[0]
        name_with_rating = self.game_list.get(index)
        game_name = name_with_rating.split(" (")[0]
        if messagebox.askyesno("Подтверждение", f"Удалить '{game_name}'?"):
            for gid, game in self.library.games.items():
                if game.name == game_name:
                    self.library.remove(gid)
                    break
            self.update_list()
            self.name_label.config(text="Название: не выбрано")
            self.genre_label.config(text="Жанры: не выбрано")
            self.stats_label.config(text="Запусков: 0 | Рейтинг: 0.0")

    def launch_game(self, event=None):
        selection = self.game_list.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите игру")
            return

        index = selection[0]
        name_with_rating = self.game_list.get(index)
        game_name = name_with_rating.split(" (")[0]
        for game in self.library.get_all():
            if game.name == game_name:
                if game.launch():
                    messagebox.showinfo("Успех", f"Запускаем {game.name}")
                    self.update_list()
                    self.select_game()
                else:
                    messagebox.showerror("Ошибка", "Не удалось запустить!")
                break

    def rate_game(self):
        selection = self.game_list.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите игру")
            return
        index = selection[0]
        name_with_rating = self.game_list.get(index)
        game_name = name_with_rating.split(" (")[0]
        rating = simpledialog.askfloat("Оценка", "Оценка от 1 до 5:",
                                       minvalue=1.0, maxvalue=5.0, initialvalue=0.0)

        if rating:
            for game in self.library.get_all():
                if game.name == game_name:
                    game.set_rating(rating)
                    self.library.save()
                    self.update_list()
                    self.select_game()
                    messagebox.showinfo("Готово", f"Оценка сохранена: {rating:.1f}")
                    break

    def show_recommendations(self):
        recommendations = self.library.get_recommendations(3)
        self.rec_text.delete(1.0, tk.END)
        if not recommendations:
            self.rec_text.insert(tk.END, "Добавьте больше игр для рекомендаций")
            return

        self.rec_text.insert(tk.END, "рекомендуем поиграть:\n\n")
        for i, game in enumerate(recommendations, 1):
            genres = ", ".join(game.genres) if game.genres else "разные"
            self.rec_text.insert(tk.END,
                                 f"{i}. {game.name}\n"
                                 f"   Жанры: {genres}\n"
                                 f"   Оценка: {game.rating:.1f}/5\n"
                                 f"   Запусков: {game.play_count}\n\n"
                                 )
    def launch_random(self):
        games = self.library.get_all()
        if not games:
            messagebox.showwarning("Ошибка", "Нет игр в библиотеке")
            return

        game = random.choice(games)
        if game.launch():
            messagebox.showinfo("Успех", f"Запускаем {game.name}!")
            self.update_list()
        else:
            messagebox.showerror("Ошибка", "Не удалось запустить!")

    def run(self):
        self.window.mainloop()

def main():
    app = GameLauncherApp()
    app.run()

if __name__ == "__main__":
    main()
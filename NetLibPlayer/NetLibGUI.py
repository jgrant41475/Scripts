from pyforms import start_app
from pyforms.basewidget import BaseWidget
from pyforms.controls import ControlText, ControlButton, ControlList
from sys import exit
from NetLibPlayer.config import media_root, vlc_path, playable_extensions
from os import scandir
from subprocess import run, Popen, CREATE_NEW_CONSOLE


class NetLibGUI(BaseWidget):
    def __init__(self):
        super(NetLibGUI,self).__init__('Network Library')

        movieList = ControlList("Movies")
        movieList.readonly = True
        movieList.value = []
        movieList.cell_double_clicked_event = self.__movieListDoubleClicked
        
        tvSeriesList = ControlList("Series")
        tvSeriesList.readonly = True
        tvSeriesList.value = []
        tvSeriesList.cell_double_clicked_event = self.__seriesListDoubleClicked

        tvSeasonsList = ControlList("Seasons")
        tvSeasonsList.readonly = True
        tvSeasonsList.value = []
        tvSeasonsList.cell_double_clicked_event = self.__seasonsListDoubleClicked

        tvEpisodesList = ControlList("Episodes")
        tvEpisodesList.readonly = True
        tvEpisodesList.value = []
        tvEpisodesList.cell_double_clicked_event = self.__episodesListDoubleClicked

        self.library = {}
        self._movieList = movieList
        self._tvSeriesList = tvSeriesList
        self._tvSeasonsList = tvSeasonsList
        self._tvEpisodesList = tvEpisodesList

        self.formset = [ { 
            'Movies': ['_movieList'],
            'TV': [('_tvSeriesList', '||', '_tvSeasonsList', '||', '_tvEpisodesList')],
        } ]

        self.mainmenu = [
            { 'File': [
                { 'Reload': self.__loadMedia },
                '-',
                { 'Quit': exit }
            ] }
        ]

        if media_root:
            self.__loadMedia()

    def __loadMedia(self):
        self.library = {}
        self._movieList.value = []
        self._tvSeriesList.value = []
        self._tvSeasonsList.value = []
        self._tvEpisodesList.value = []
        self.selected_series = None
        self.selected_season = None
        self.selected_episode = None

        with scandir(media_root + "Movies/") as movie_root:
            movieTemp = []
            for movie_folder in movie_root:
                with scandir(movie_folder.path) as movie:
                    movie_file = [f for f in movie if f.name[-3:] in playable_extensions]
                    if movie_file and len(movie_file) > 0:
                        movieTemp.append([movie_folder.name, movie_file[0].path])
                    
            self.library["movies"] = [{"name": entry[0], "path": entry[1].replace("/", "\\\\")} for entry in movieTemp]
        
        with scandir(media_root + "TV/") as tv_root:
            showTemp = []
            seasonList = []
            episodeList = []
            for show_folder in tv_root:
                seasonList = []
                with scandir(show_folder.path) as seasons:
                    for season in seasons:
                        episodeList = []
                        with scandir(season.path) as episodes:
                            [episodeList.append({"name": episode.name, "path": episode.path}) for episode in episodes]
                        seasonList.append({"name": season.name, "episodes": episodeList})
                    showTemp.append({"name": show_folder.name, "seasons": seasonList})
        
            self.library["shows"] = showTemp

        self._movieList.value = [[entry["name"]] for entry in self.library["movies"]]
        self._tvSeriesList.value = list(map(lambda x: [x["name"]], showTemp))

    def __movieListDoubleClicked(self, row, column):
        Popen([vlc_path, self.library["movies"][row]["path"], "-f"], creationflags=CREATE_NEW_CONSOLE)
    
    def __seriesListDoubleClicked(self, row, column):
        series = self.library["shows"][row]
        self.selected_series = row
        self.selected_episode = None
        self.selected_season = None
        self._tvSeasonsList.value = list(map(lambda x: [x["name"]], series["seasons"]))
        self._tvEpisodesList.value = []
    
    def __seasonsListDoubleClicked(self, row, colum):
        season = self.library["shows"][self.selected_series]["seasons"][row]
        self.selected_season = row
        self.selected_episode = None
        self._tvEpisodesList.value = list(map(lambda x: [x["name"]], season["episodes"]))
    
    def __episodesListDoubleClicked(self, row, column):
        self.selected_episode = row
        Popen([vlc_path, 
            self.library["shows"][self.selected_series]
                        ["seasons"][self.selected_season]
                        ["episodes"][self.selected_episode]
                        ["path"].replace("/", "\\"), "-f"], 
            creationflags=CREATE_NEW_CONSOLE)


if __name__ == "__main__":
    start_app(NetLibGUI, geometry=(150, 150, 600, 600))

import tornado.ioloop 
import tornado.web
import signal, os
from jinja2 import Environment, PackageLoader
import pandas as pd
import numpy as np
from nbastats import plotting

YEARS = xrange(2000, 2015)
TEMPLATE_DIR = 'templates'
PKG = 'nbastats'
POSITIONS = {'c':'Center', 'pf':'Power Forward', 'sf':'Small Forward', 'sg':'Shooting Guard', 'pg':'Point Guard', 'all':'All Players'}
STATS = ['PPG', 'RPG', 'APG', 'SPG', 'BPG']

def render_leaders(stats, n_top, year, temp_dir, temp_file, position):
    """ take in a dataframe, return rendered templates with data of top player stats in PTS, REB, AST, STL, and BLK """
    leader_stats = []
    plots = []
    for stat in STATS:
        leader_stats.append(stats.sort(stat, ascending=False)[:n_top].to_dict(orient='record'))
        plots.append(plotting.hist_plot(np.array(stats[stat]), '{} Distribution in the League'.format(stat)))
    env = Environment(loader=PackageLoader(PKG, temp_dir))
    template = env.get_template(temp_file)
    
    return template.render(data=leader_stats, years=YEARS, year=year, season='{}-{}'.format(int(year)-1, year), position=POSITIONS[position], plots=plots)

def render_players(players, position, option, temp_dir, temp_file):
    """ """
    players_in_pos = np.array(players.PLAYER[players['POS']==position.upper()])
    n = len(players_in_pos)
    players_cols = [players_in_pos[:n/4+1], players_in_pos[(n/4+1):(n/2+2)], players_in_pos[(n/2+2):(3*n/4+3)], players_in_pos[(3*n/4+3):]]
    count = np.array(players.groupby('POS').count()['PLAYER'][['C', 'PF', 'SF', 'SG', 'PG']])
    env = Environment(loader=PackageLoader(PKG, temp_dir))
    template = env.get_template(temp_file)
    return template.render(option=option, position=position, count=count, players=players_cols)

class OverviewHandler(tornado.web.RequestHandler):
    """ Request Handler for /overview/year """
    def get(self, year=2014):
        try:
            filename = 'nbastats/static/data/stats_{}.csv'.format(year)
            stats = pd.read_csv(filename)
        except IOError:
            print 'data not found'
            raise tornado.web.HTTPError(500)

        self.write(render_leaders(stats, 12, year, TEMPLATE_DIR, 'overview.html', 'all'))

class PositionHandler(tornado.web.RequestHandler):
    """ Request handler for /overview/year/position """
    def get(self, year, position):
        try:
            stats = pd.read_csv('nbastats/static/data/stats_{}.csv'.format(year))
        except IOError:
            print 'data not found'
            raise tornado.web.HTTPError(500)
        pos = position.upper()
        self.write(render_leaders(stats[stats.POS==pos], 8, year, TEMPLATE_DIR, 'overview.html', position))

class PlayersListHandler(tornado.web.RequestHandler):
    """ Request handler for /players/name """
    def get(self, option, position):
        try:
            players = pd.read_csv('nbastats/static/data/players_{}.csv'.format(option))
        except IOError:
            raise tornado.web.HTTPError(500)
        
        self.write(render_players(players, position, option, TEMPLATE_DIR, 'players_index.html'))
        
class PlayersOverviewHandler(tornado.web.RequestHandler):
    """ """
    def get(self):
        pass
    
def make_app():
    settings = {"debug": True,
                "static_path": os.path.join(os.path.dirname(__file__), "nbastats/static"),}

    return tornado.web.Application([
        (r'/static/(.*)', tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
        (r'/overview/(20[01][0-9])', OverviewHandler),
        (r'/overview/(20[01][0-9])/(c|pf|sf|sg|pg)', PositionHandler),
        (r'/players/(current|historic)/(c|pf|sf|sg|pg)', PlayersListHandler),
        (r'/overview', tornado.web.RedirectHandler, {'url': '/overview/2014'}),
        (r'/players/current', tornado.web.RedirectHandler, {'url': '/players/current/c'}),
        (r'/players/historic', tornado.web.RedirectHandler, {'url': '/players/historic/c'}),
        (r'/players/info', PlayersOverviewHandler),
    ], **settings)

def on_shutdown():
    print 'Shutting down'
    tornado.ioloop.IOLoop.instance().stop()

def main():
    app = make_app()
    app.listen(8888)
    ioloop = tornado.ioloop.IOLoop.instance()
    signal.signal(signal.SIGINT, lambda sig, frame: ioloop.add_callback_from_signal(on_shutdown))
    ioloop.start()

if __name__ == '__main__':
    main()

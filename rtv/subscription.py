import curses

from .content import SubscriptionContent
from .page import BasePage, Navigator, BaseController
from .terminal import Color, LoadScreen


class SubscriptionController(BaseController):
    character_map = {}


class SubscriptionPage(BasePage):

    def __init__(self, stdscr, reddit, config, oauth):

        super(SubscriptionPage, self).__init__(stdscr, reddit, config, oauth)

        self.content = SubscriptionContent.from_user(reddit, self.loader)
        self.controller = SubscriptionController(self)
        self.nav = Navigator(self.content.get)
        self.subreddit_data = None

    def loop(self):
        "Main control loop"

        self.active = True
        while self.active:
            self.draw()
            cmd = self.stdscr.getch()
            self.controller.trigger(cmd)

    @SubscriptionController.register(curses.KEY_F5, 'r')
    def refresh_content(self, order=None):
        "Re-download all subscriptions and reset the page index"

        # reddit.get_my_subreddits() does not support sorting by order
        if order:
            curses.flash()
            return

        self.content = SubscriptionContent.from_user(self.reddit, self.loader)
        self.nav = Navigator(self.content.get)

    @SubscriptionController.register(curses.KEY_ENTER, 10, curses.KEY_RIGHT)
    def store_selected_subreddit(self):
        "Store the selected subreddit and return to the subreddit page"

        self.subreddit_data = self.content.get(self.nav.absolute_index)
        self.active = False

    @SubscriptionController.register(curses.KEY_LEFT, 'h', 's')
    def close_subscriptions(self):
        "Close subscriptions and return to the subreddit page"

        self.active = False

    def draw_item(self, win, data, inverted=False):
        n_rows, n_cols = win.getmaxyx()
        n_cols -= 1  # Leave space for the cursor in the first column

        # Handle the case where the window is not large enough to fit the data.
        valid_rows = range(0, n_rows)
        offset = 0 if not inverted else -(data['n_rows'] - n_rows)

        row = offset
        if row in valid_rows:
            attr = curses.A_BOLD | Color.YELLOW
            self.add_line(win, u'{name}'.format(**data), row, 1, attr)

        row = offset + 1
        for row, text in enumerate(data['split_title'], start=row):
            if row in valid_rows:
                self.add_line(win, text, row, 1)
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import praw
import curses

from rtv.subscription import SubscriptionPage

try:
    from unittest import mock
except ImportError:
    import mock


def test_subscription_page_draw(reddit, terminal, config, oauth, refresh_token):

    window = terminal.stdscr.subwin

    # Log in
    config.refresh_token = refresh_token
    oauth.authorize()
    with terminal.loader():
        page = SubscriptionPage(reddit, terminal, config, oauth)
    assert terminal.loader.exception is None

    page.draw()

    # Header - Title
    title = 'Subscriptions'.encode('utf-8')
    window.addstr.assert_any_call(0, 0, title)

    # Header - Name
    name = reddit.user.name.encode('utf-8')
    window.addstr.assert_any_call(0, 59, name)

    # Cursor - 2 lines
    window.subwin.chgat.assert_any_call(0, 0, 1, 262144)
    window.subwin.chgat.assert_any_call(1, 0, 1, 262144)

    # Reload with a smaller terminal window
    terminal.stdscr.ncols = 20
    terminal.stdscr.nlines = 10
    with terminal.loader():
        page = SubscriptionPage(reddit, terminal, config, oauth)
    assert terminal.loader.exception is None

    page.draw()


def test_subscription_page(reddit, terminal, config, oauth, refresh_token):

    # Can't load the page if not logged in
    with terminal.loader():
        SubscriptionPage(reddit, terminal, config, oauth)
    assert isinstance(
        terminal.loader.exception, praw.errors.LoginOrScopeRequired)

    # Log in
    config.refresh_token = refresh_token
    oauth.authorize()
    with terminal.loader():
        page = SubscriptionPage(reddit, terminal, config, oauth)
    assert terminal.loader.exception is None

    # Refresh content - invalid order
    page.controller.trigger('2')
    assert curses.flash.called
    curses.flash.reset_mock()

    # Refresh content
    page.controller.trigger('r')
    assert not curses.flash.called

    page.draw()

    # Move cursor to the bottom of the page
    while not curses.flash.called:
        page.controller.trigger('j')
    curses.flash.reset_mock()
    assert page.nav.absolute_index == 52  # 52 total subscriptions
    assert page.nav.inverted

    # And back to the top
    for i in range(page.nav.absolute_index):
        page.controller.trigger('k')
    assert not curses.flash.called
    assert page.nav.absolute_index == 0
    assert not page.nav.inverted

    # Can't go up any further
    page.controller.trigger('k')
    assert curses.flash.called
    assert page.nav.absolute_index == 0
    assert not page.nav.inverted

    # All subscriptions should have been loaded, including this one
    window = terminal.stdscr.subwin.subwin
    name = 'Python'.encode('utf-8')
    window.addstr.assert_any_call(1, 1, name)

    # Page down should move the last item to the top
    n = len(page._subwindows)
    page.controller.trigger('n')
    assert page.nav.absolute_index == n - 1

    # And page up should move back up, but possibly not to the first item
    page.controller.trigger('m')

    # Select a subreddit
    page.controller.trigger(curses.KEY_ENTER)
    assert page.subreddit_data is not None
    assert page.active is False

    # Close the subscriptions page
    page.subreddit_data = None
    page.active = None
    page.controller.trigger('h')
    assert page.subreddit_data is None
    assert page.active is False

    # Test that other commands don't crash
    methods = [
        'a',  # Upvote
        'z',  # Downvote
        'd',  # Delete
        'e',  # Edit
    ]
    for ch in methods:
        curses.flash.reset_mock()
        page.controller.trigger(ch)
        assert curses.flash.called
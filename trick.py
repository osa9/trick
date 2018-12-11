from argparse import ArgumentParser
import getpass
import requests
import json
from dateutil.parser import parse
from pytz import timezone

API_ENDPOINT = 'https://trickle-api.appspot.com'


class Trick:
    def __init__(self, auth=None, access_token=None, me=None, endpoint=API_ENDPOINT):
        self.endpoint = endpoint

        if access_token:
            self.access_token = access_token
            self.me = me
        elif auth:
            self.access_token = self.login(auth[0], auth[1])['accessToken']

    def _headers(self, auth):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache',
        }
        if auth:
            headers['Authorization'] = "Bearer " + self.access_token
        return headers

    def _post(self, path, data, auth=True):
        headers = self._headers(auth)
        r = requests.post(API_ENDPOINT + path,
                          headers=headers, data=json.dumps(data))
        if r.status_code != 200:
            raise Exception(
                'Request Error(status_code={})'.format(r.status_code))
        return r.json()

    def _get(self, path, data=None, auth=True):
        headers = self._headers(auth)
        endpoint = API_ENDPOINT + path
        if data:
            endpoint = endpoint + '?json=' + json.dumps(data)
        r = requests.get(endpoint, headers=headers)
        if r.status_code != 200:
            print(r)
            raise Exception(
                'Request Error(status_code={})'.format(r.status_code))
        return r.json()

    def login(self, user, password):
        r = self._post('/v1/auth/sign_in',
                       {'name': user, 'password': password}, auth=False)
        if not r['success']:
            raise Exception('Request is not succeeded')
        self.me = r['user']
        return r

    def get_activity(self, activity_id):
        return self._get('/v1/activities', {'id': activity_id})

    def get_user_activities(self, user_id):
        return self._get('/v1/activities/index', {'userId': user_id})

    def get_topic_activities(self, topic_id):
        return self._get('/v1/activities/index_by_topic', {'topicId': topic_id})

    def get_topic(self, topic_id):
        return self._get('/v1/topics', {'id': topic_id})

    def get_user_topics(self, user_id):
        return self._get('/v1/topics/index', {'userId': user_id, 'page': 0, 'perPage': 20})


def login(userid):
    password = getpass.getpass()
    trick = Trick(auth=[userid, password])
    me = trick.me
    session = {
        'me': trick.me,
        'access_token': trick.access_token
    }
    print('Login success!\nNAME: {}\nID: {}'.format(me['name'], me['id']))
    with open('session.json', 'w') as f:
        f.write(json.dumps(session))
    return trick


def restore_session():
    try:
        session = json.load(open('session.json'))
        return Trick(access_token=session['access_token'], me=session['me'])
    except:
        return None


def list_topics(trick, user_id):
    topics = trick.get_user_topics(user_id)
    for topic in topics['topics']:
        print('{}(topic_id={})'.format(topic['title'], topic['id']))


def list_activities(trick, user_id=None, topic_id=None):
    if topic_id:
        activities = trick.get_topic_activities(topic_id)
    else:
        activities = trick.get_user_activities(user_id)
    for activity in activities['activities']:
        createdAt = parse(activity['createdAt']).astimezone(
            timezone('Asia/Tokyo'))
        print('{}'.format(createdAt))
        print('topic={}(topic_id={})'.format(
            activity['topic']['title'], activity['topic']['id']))
        print('{}'.format(activity['memo']))
        print()


def main():
    usage = 'Usage: python {} login --userid userid/list-topic/list-activity --topic_id=[topic_id] '\
            .format(__file__)
    argparser = ArgumentParser(usage=usage)
    argparser.add_argument('command', type=str,
                           help='command')
    argparser.add_argument('-u', '--userid', type=str,
                           help='userid')
    argparser.add_argument('-p', '--password', type=str,
                           help='password')
    argparser.add_argument('-a', '--access_token', type=str,
                           help='if access token is specified, skip login phase')
    argparser.add_argument('-t', '--topic_id', type=int,
                           help='topic id')
    args = argparser.parse_args()

    if args.command == 'login':
        login(args.userid)
        return

    trick = restore_session()
    if not trick:
        print('Need to login')
        return

    if args.command == 'list-topic':
        list_topics(trick, trick.me['id'])
        return
    elif args.command == 'list-activity':
        if args.topic_id:
            list_activities(trick, topic_id=args.topic_id)
        else:
            list_activities(trick, user_id=trick.me['id'])
    else:
        print('Unknown command {}'.format(args.command))


if __name__ == '__main__':
    main()

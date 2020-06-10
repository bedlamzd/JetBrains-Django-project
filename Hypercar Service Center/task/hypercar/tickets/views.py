from django.views import View
from django.views.generic.base import TemplateView
from django.http.response import HttpResponse
from django.shortcuts import render, redirect

services_data = {'change_oil': {'client_text': 'Change oil',
                                'employee_text': 'Change oil queue',
                                'priority': 1,
                                'wait_time': 2},
                 'inflate_tires': {'client_text': 'Inflate tires',
                                   'employee_text': 'Inflate tires queue',
                                   'priority': 2,
                                   'wait_time': 5},
                 'diagnostic': {'client_text': 'Get diagnostic test',
                                'employee_text': 'Get diagnostic queue',
                                'priority': 3,
                                'wait_time': 30}}


class id_tracker:
    id = 0
    _next_idx = None

    def __call__(self, *args, **kwargs):
        return self.id

    def add(self):
        self.id += 1

    @property
    def next_in_queue(self):
        return self._next_idx

    @next_in_queue.setter
    def next_in_queue(self, idx):
        self._next_idx = idx


idx = id_tracker()


class Service:
    def __init__(self, name: str, link=None, priority=0, wait_time=0, queue=None, client_text='',
                 employee_text=''):
        self.name = name
        self.link = link if link is not None else name.lower().replace(' ', '-')
        self.priority = priority
        self.wait_time = wait_time
        self.queue = queue if queue else []
        self.client_text = client_text
        self.employee_text = employee_text

    def add(self):
        idx.add()
        self.queue.append(idx())

    @property
    def people(self):
        return len(self.queue)


class ServicesWrapper(dict):
    def __init__(self, *args, **kwargs):
        super(ServicesWrapper, self).__init__(*args, **kwargs)

    @property
    def next_in_queue(self):
        for service in sorted(self.values(), key=lambda service: service.priority):
            try:
                return service.queue[0]
            except IndexError:
                pass
        return None

    def pop_queue(self):
        for service in sorted(self.values(), key=lambda service: service.priority):
            try:
                idx = service.queue.pop(0)
                return idx
            except IndexError:
                pass
        return None

    def waiting_time(self, service):
        return sum(data.people * data.wait_time for data in self.values() if
                   data.priority <= self[service].priority)


services = ServicesWrapper({
    'change_oil': Service('Change oil', 'change_oil', **services_data['change_oil']),
    'inflate_tires': Service('Inflate tires', 'inflate_tires', **services_data['inflate_tires']),
    'diagnostic': Service('Diagnostic test', 'diagnostic', **services_data['diagnostic']), })


class WelcomeView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('<h2>Welcome to the Hypercar Service!</h2>')


class MenuView(View):
    template_name = 'tickets/menu.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, context={'services': services})


class TicketView(TemplateView):
    template_name = 'tickets/ticket.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = kwargs['service']
        context['title'] = services[service].name
        context['waiting_time'] = services.waiting_time(service)
        services[service].add()
        context['idx'] = idx()
        return context


class ProcessingView(View):
    template_name = 'tickets/processing.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, context={'services': services})

    def post(self, request, *args, **kwargs):
        idx.next_in_queue = services.pop_queue()
        return redirect('/next')


class NextView(View):
    template_name = 'tickets/next.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, context={'next_idx': idx.next_in_queue})

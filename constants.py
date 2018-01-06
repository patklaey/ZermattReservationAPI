# coding=utf-8
PASSWORD_MIN_LENGTH = 8

MAIL_MESSAGES = {
    'de': {
        'registration' : {
            'subject': "Registration auf zermatt.patklaey.ch",
            'message': "Hallo {}\n\nVielen Dank für die Registrierung, dein Konto wird bald aktiviert. Du wirst ein weiteres Mail mit der Aktivierungsbestäting für dein Konto erhalten.\n\nZermatt Reservationen"
        },
        'activation' : {
            'subject' : "Konto auf zermatt.patklaey.ch aktiviert",
            'message' : "Hallo {}\n\nDein Konto wurde soeben von einem Administrator aktiviert. Du kannst dich ab sofort auf https://zermatt.patklaey.ch einloggen und reservationen tätigen.\n\nViel Spass.\n\nZermatt Reservationen"
        },
        'reminder' : {
            'subject' : "Deine nächste Reservation in Zermatt",
            'message' : "Hallo {}\n\nDeine nächste Reservation in Zermatt ist am {}, das ist in weniger als zwei Tagen. Diese Mail dient nur als freundliche Erinnerung, aber falls sich deine Pläne geändert haben bitte lösche die Reservation damit andere die Möglichkeit haben, das Matterhorn zu sehen :-)\n\nZermatt Reservationen"
        }
    },
    'de-be': {
        'registration' : {
            'subject': "Registration uf zermatt.patklaey.ch",
            'message': "Hallo {}\n\nMerci viu mau für d Registrierig, dis Konto wird gli aktiviert. Du wirsch es witers Mail mit dr Aktivierigsbestätigung für dis Konto becho.\n\nZermatt Reservatione"
        },
        'activation' : {
            'subject' : "Konto uf zermatt.patklaey.ch isch aktiviert",
            'message' : "Hallo {}\n\nDis Konto isch grad vomene Administrator aktiviert worde. Du chasch di ab sofort uf https://zermatt.patklaey.ch ilogge u reservatione tätige.\n\nViu Spass.\n\nZermatt Reservatione"
        },
        'reminder' : {
            'subject' : "Dini nächschti Reservation in Zermatt",
            'message' : "Hallo {}\n\nDini nächschti Reservation in Zermatt isch am {}, das isch i weniger aus zwe täg. Das mail dient nume aus fründlechi Erinnerig, aber faus sech dini Plän gänderet hei bitte lösch doch d Reservation so dass o anderi d müglechkeit hei, ds Matterhorn ds gse :-)\n\nZermatt Reservatione"
        }
    },
    'en': {
        'registration' : {
            'subject': "SignUp on zermatt.patklaey.ch",
            'message': "Hello {}\n\nThank you for signing up, your account will be activated soon. You will get another mail confirming the account activation.\n\nZermatt Reservations"
        },
        'activation' : {
            'subject' : "Account on zermatt.patklaey.ch activated",
            'message' : "Hello {}\n\nYour account has just been activated. You can now login on https://zermatt.patklaey.ch and add reservations.\n\nHave fun\n\nZermatt Reservations"
        },
        'reminder' : {
            'subject' : "Your next reservation in Zermatt",
            'message' : "Hello {}\n\nYour next reservation in Zermatt is on {}, which is in less than two days from now. This mail is only a friendly reminder, but if your plans have changed, please remove the reservation in order to allow others to see the Matterhorn :-)\n\nZermatt Reservations"
        }
    }
}
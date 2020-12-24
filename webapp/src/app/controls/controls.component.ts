import {Component, OnInit} from '@angular/core';
import {OptionsComponent} from '../options/options.component';
import {MatDialog} from '@angular/material/dialog';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {DisplayComponent} from '../display/display.component';
import {AppComponent} from '../app.component';
import {Router, ActivatedRoute, Params} from '@angular/router';
import {MessageComponent} from '../message/message.component';
import {DetailsComponent} from '../details/details.component';

@Component({
  selector: 'app-controls',
  templateUrl: './controls.component.html',
  styleUrls: ['./controls.component.css']
})
export class ControlsComponent implements OnInit
{
  public static singleton: ControlsComponent;


  /* error messages */
  errorMessages = [];

  /* default values are not a valid request */
  invalidRequest = true;

  /* a default start date */
  startDate = new Date(2015, 0, 1); /* 2015-JAN-01 */

  /* a default end date */
  endDate = new Date(2015, 0, 31); /* 2015-JAN-31 */

  /* variable to store the date help HTML */
  dateHelp = 'assets/date_help.html';

  /* cycle options */
  c00z = true;
  c06z = false;
  c12z = false;
  c18z = false;

  /* norm options */
  private norm = {};

  /* center options */
  private centers = {};

  /* platform options */
  private platforms = {};

  /* default summaries */
  normSummary = '(0) No selections made';
  centersSummary = '(0) No selections made';
  platformsSummary = '(0) No selections made';

  /* reference to app component */
  app: AppComponent;

  /* Object that contains a request to the server */
  private requestData: object;

  /* Websocket connection */
  private websocket: WebSocket;
  // private websocketUrl = 'wss://bj2c69kuw2.execute-api.us-east-1.amazonaws.com/v2'; // BETA
  private websocketUrl = 'wss://prw9exvaxi.execute-api.us-east-1.amazonaws.com/v2'; // OPS

  /* these headers can be added to an HTTP request to prevent using cached responses */
  private noCacheHeaders: HttpHeaders;

  /* Track all requests in this session */
  sessionRequests = [];


  /**
   * Constructor
   *
   * @param dialog dependency injection
   * @param http dependency injection
   * @param route dependency injection
   */
  constructor(private dialog: MatDialog, private http: HttpClient, private route: ActivatedRoute)
  {
    ControlsComponent.singleton = this;
    this.noCacheHeaders = new HttpHeaders({
      'Cache-Control': 'no-cache, no-store, must-revalidate, post-check=0, pre-check=0',
      'Pragma': 'no-cache',
      'Expires': '0'
    });
  }

  /**
   * Convert a date to a string
   *
   * @param date in the format yyyyMMdd
   */
  static dateToString(date): string
  {
    return date.getFullYear() + '' + ('0' + (date.getMonth() + 1)).slice(-2) + ('0' + date.getDate()).slice(-2);
  }


  /**
   * Initialize the component
   */
  ngOnInit()
  {
    this.loadOptions();
    this.loadDateHelp();
    this.route.queryParams.subscribe(this.queryParamsChanged.bind(this));
  }


  /**
   * Make an HTTP GET request to the assets/options.json file
   */
  loadOptions(): void
  {
    this.http.get('assets/options.json', {headers: this.noCacheHeaders}).subscribe(this.optionsLoaded.bind(this));
  }


  /**
   * We have received data from the options.json file, update the member variables in this class
   *
   * @param data Contains the options data
   */
  optionsLoaded(data): void
  {
    this.centers = data.centers;
    this.platforms = data.platforms;
    this.norm = data.norm;
    this.updateSummaries();
    this.validateRequest();
  }


  /**
   * Load date help
   */
  loadDateHelp(): void
  {
    this.http.get('assets/date_help.html', {headers: this.noCacheHeaders, responseType: 'text'}).subscribe(this.dateHelpLoaded.bind(this));
  }


  /**
   * Put the date help into the right variable to be displayed
   *
   * @param data The HTML containing help on dates
   */
  dateHelpLoaded(data): void
  {
    this.dateHelp = data;
  }


  /**
   * Set a reference to the app component
   *
   * @param app Reference to the app component
   */
  setApp(app: AppComponent): void
  {
    this.app = app;
  }


  /**
   * Update summaries for all choice options (i.e., string label based on selected choices)
   */
  updateSummaries(): void
  {
    this.normSummary = this.createSummary(this.norm);
    this.centersSummary = this.createSummary(this.centers);
    this.platformsSummary = this.createSummary(this.platforms);
  }


  /**
   * Show day/night maps when mouse moves into a cycle checkbox
   *
   * @param cycle The cycle to show
   */
  showCycleHint(cycle): void
  {
    document.getElementById('cycle_hint').setAttribute('src', 'assets/hint-' + cycle + 'z.jpg');
  }


  /**
   * Hide day/night maps when mouse moves out of a cycle checkbox
   */
  clearCycleHint(): void
  {
    document.getElementById('cycle_hint').setAttribute(
      'src',
      'data:image/gif;base64,R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
    );
  }


  /**
   * Look through the data object and create a summary including the number
   * of selected items and a comma-separated list of the selected items.
   *
   * @param data An object from which to create a summary
   */
  createSummary(data: object): string
  {
    /* init string and count variables */
    let summary = '';
    let count = 0;

    /* if no selections are made */
    if (data['options'] === undefined)
    {
      return '(0)';
    }

    /* build a string and count the number of options selected */
    for (let j = 0; j < data['options'].length; j++)
    {
      const item = data['options'][j];

      if (item['selected'] === true)
      {
        count++;
        if (count > 1)
        {
          summary += ', ';
        }
        summary += item['name'];
      }
    }
    return '(' + count + ') ' + summary;
  }


  /**
   * Show a modal dialog with the available options
   */
  showOptionDialog(option: string, selectMultiple: boolean): void
  {
    let data;

    switch (option)
    {
      case 'norm':
        data = this.norm;
        break;
      case 'center':
        data = this.centers;
        break;
      case 'platform':
        data = this.platforms;
        break;
    }

    if (data === undefined)
    {
      console.log('Invalid option set: ' + option);
      return;
    }

    const dialogRef = this.dialog.open(OptionsComponent, {
      width: '600px',
      height: '800px',
      data: {'title': option + 's', 'list': data, 'selectMultiple': selectMultiple}
    });

    dialogRef.afterClosed().subscribe(result =>
      {
        this.updateSummaries();
        this.validateRequest();
      }
    );
  }


  /**
   * Validate the request based on current selections
   */
  validateRequest(): void
  {
    this.errorMessages = [];

    /* validate the dates */
    if (this.startDate === undefined || this.endDate === undefined)
    {
      this.errorMessages[this.errorMessages.length] = 'start and end dates are required';
    } else if (this.startDate.getTime() > this.endDate.getTime())
    {
      this.errorMessages[this.errorMessages.length] = 'end date must not be earlier than start date';
    }

    /* validate the cycles */
    if (!this.c00z && !this.c06z && !this.c12z && !this.c18z)
    {
      this.errorMessages[this.errorMessages.length] = 'at least one cycle must be selected';
    }

    /* validate the norms */
    let norms = 0;
    for (let i = 0; i < this.norm['options'].length; i++)
    {
      if (this.norm['options'][i]['selected'])
      {
        norms++;
      }
    }
    if (norms > 1)
    {
      this.errorMessages[this.errorMessages.length] = 'only one norm may be selected';
    } else if (norms === 0)
    {
      this.errorMessages[this.errorMessages.length] = 'at least one norm must be selected';
    }

    /* validate the centers */
    let centers = 0;
    for (let i = 0; i < this.centers['options'].length; i++)
    {
      if (this.centers['options'][i]['selected'])
      {
        centers++;
      }
    }
    if (centers === 0)
    {
      this.errorMessages[this.errorMessages.length] = 'at least one center must be selected';
    }

    /* validate the platforms */
    let platforms = 0;
    if (this.platforms['options'] !== undefined)
    {
      for (let i = 0; i < this.platforms['options'].length; i++)
      {
        if (this.platforms['options'][i]['selected'])
        {
          platforms++;
        }
      }
    }
    if (platforms === 0)
    {
      this.errorMessages[this.errorMessages.length] = 'one or more platforms must be selected';
    }

    this.invalidRequest = this.errorMessages.length > 0;
  }


  /**
   * Change the date
   *
   * @param event Details including target and value
   */
  changeDate(event): void
  {
    if (event['targetElement']['placeholder'] === 'Start Date')
    {
      this.startDate = event['value'];
    } else if (event['targetElement']['placeholder'] === 'End Date')
    {
      this.endDate = event['value'];
    } else
    {
      console.log('Date change event ignored.');
      console.log(event);
    }

    this.validateRequest();
  }


  /**
   * Send a request to the API
   */
  submitRequest(): void
  {
    /* Query string parameters */
    const startDate = ControlsComponent.dateToString(this.startDate);
    const endDate = ControlsComponent.dateToString(this.endDate);

    /* add centers */
    let centers = '';
    for (let i = 0; i < this.centers['options'].length; i++)
    {
      if (this.centers['options'][i]['selected'] === true)
      {
        centers += this.centers['options'][i]['name'] + ',';
      }
    }
    centers = centers.slice(0, -1);

    /* add norms */
    let norm = '';
    for (let i = 0; i < this.norm['options'].length; i++)
    {
      if (this.norm['options'][i]['selected'] === true)
      {
        norm += this.norm['options'][i]['name'] + ',';
      }
    }
    norm = norm.slice(0, -1);

    /* add platforms */
    let platforms = '';
    for (let i = 0; i < this.platforms['options'].length; i++)
    {
      if (this.platforms['options'][i]['selected'] === true)
      {
        platforms += this.platforms['options'][i]['name'] + ',';
      }
    }
    platforms = platforms.slice(0, -1);

    /* add the cycles */
    let cycles = '';
    if (this.c00z)
    {
      cycles += '0,';
    }
    if (this.c06z)
    {
      cycles += '6,';
    }
    if (this.c12z)
    {
      cycles += '12,';
    }
    if (this.c18z)
    {
      cycles += '18,';
    }
    cycles = cycles.slice(0, -1);

    /* construct the request */
    this.requestData = {
      'start_date': startDate,
      'end_date': endDate,
      'centers': centers,
      'norm': norm,
      'platforms': platforms,
      'cycles': cycles,
      'interval': 24
    };

    /* send the request over the websocket */
    this.sendMessage(this.requestData);
  }


  /**
   * Get a websocket connection -- create one if it does not already exist
   */
  getWebSocketConnection(): WebSocket
  {
    if (this.websocket === undefined)
    {
      /* create a new websocket */
      this.websocket = new WebSocket(this.websocketUrl);

      /* add listeners for the new websocket */
      this.websocket.onopen = function() { console.log('Websocket connection opened.'); };
      this.websocket.onclose = function() { this.websocket = undefined; console.log('Websocket connection closed.'); }.bind(this);
      this.websocket.onmessage = this.receiveMessage.bind(this);

      return this.websocket;
    }

    /* return the websocket */
    return this.websocket;
  }


  /**
   * Send a message to the server via the websocket
   *
   * @param data The data to send
   */
  sendMessage(data: object): void
  {
    const ws = this.getWebSocketConnection();

    /* make sure the websocket is ready */
    if (ws.readyState !== 1)
    {
      setTimeout(this.sendMessage.bind(this), 200, data);
      return;
    }

    /* send data on the websocket */
    ws.send(JSON.stringify(data));
  }


  /**
   * Handle an incoming message from the server
   */
  receiveMessage(event): void
  {
    const data = JSON.parse(event.data);

    console.log(data);

    /* required a request hash for all other responses */
    if (data.req_hash === undefined)
    {
      return;
    }

    /* set warning and error flags */
    data.isComplete = data.images !== undefined;
    data.hasErrors = data.errors !== undefined && data.errors.length > 0;
    data.hasWarnings = data.warnings !== undefined && data.warnings.length > 0;

    /* find the index of this request in the sessionRequests list */
    let requestIndex = -1;
    for (let i = 0; i < this.sessionRequests.length; i++)
    {
      if (this.sessionRequests[i].req_hash === data.req_hash)
      {
        requestIndex = i;
      }
    }
    if (requestIndex === -1)
    {
      this.sessionRequests.splice(0, 0, data);
      requestIndex = 0;
    }

    /* if response contains 'images' attribute, show images and remove progress bar */
    if (data.images !== undefined)
    {
      DisplayComponent.singleton.setImages(data.images);
      this.sessionRequests[requestIndex].images = data.images;
      this.sessionRequests[requestIndex].isComplete = true;
    }

    /* if response contains 'errors' attribute, save errors on the session requests */
    else if (data.errors !== undefined)
    {
      this.sessionRequests[requestIndex].errors = data.errors;
      this.sessionRequests[requestIndex].hasErrors = true;
    }

    /* if response contains 'status_id' attribute, update status */
    else if (data.status_id !== undefined)
    {
      data.progressMode = (data.status_id === 'PENDING') ? 'indeterminate' : 'determinate';
      this.sessionRequests[requestIndex] = data;
    }

    /* if response contains 'warnings' attribute, save warnings on the session requests */
    if (data.warnings !== undefined && data.warnings.length > 0)
    {
      this.sessionRequests[requestIndex].warnings = data.warnings;
      this.sessionRequests[requestIndex].hasWarnings = true;
    }
  }


  /**
   * Show the shareable URL in a dialog
   */
  showShareUrl(shareUrl: string): void
  {
    this.dialog.open(MessageComponent, {
      width: '850px',
      height: '200px',
      data: {'title': 'Shareable URL', 'message': shareUrl}
    });
  }


  /**
   * Called by the Angular Router when query string parameters in the URL change
   *
   * @param params A list of query string parameters in the URL
   */
  queryParamsChanged(params): void
  {
    /* send a request for cached images using the params['cache_id'] value */
    this.loadCachedImages(params['cache_id']);
  }


  /**
   * Load cached images from the server
   *
   * @param cacheId The cache ID or request hash
   */
  loadCachedImages(cacheId: string): void
  {
    if (cacheId !== undefined)
    {
      this.sendMessage({'cache_id': cacheId});
    }
  }


  /**
   * Show the details of a request
   *
   * @param requestHash The hash of the request
   * @param requestObj The original request object
   * @param errors An array of strings
   * @param warnings An array of strings
   */
  showDetails(requestHash: string, requestObj: string, errors: object, warnings: object): void
  {
    this.dialog.open(DetailsComponent, {
      width: '700px',
      height: '500px',
      data: {'requestHash': requestHash, 'requestObject': requestObj, 'errors': errors, 'warnings': warnings}
    });
  }


  /**
   * Show help selecting dates
   */
  showDateHelp(): void
  {
    this.dialog.open(MessageComponent, {
      width: '850px',
      height: '425px',
      data: {'title': 'Date Selection Help', 'message': this.dateHelp, 'showCopyButton': false}
    });
  }
  /**
   * Call setTimeout since it is not available to angular
   */
  timeout(func, ms): void
  {
    setTimeout(func, ms);
  }
}

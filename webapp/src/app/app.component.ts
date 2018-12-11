import {Component, enableProdMode, ViewChild} from '@angular/core';
import {DisplayComponent} from './display/display.component';
import {ControlsComponent} from './controls/controls.component';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent
{
  @ViewChild(DisplayComponent) display: DisplayComponent;
  @ViewChild(ControlsComponent) controls: ControlsComponent;

  viewMode = 'open';

  ngOnInit()
  {
    this.controls.setDisplay(this.display);
    this.controls.setApp(this);
  }

  toggleViewMode()
  {
    this.viewMode = (this.viewMode === 'open' ? 'collapsed' : 'open');
    setTimeout(this.display.recomputeGrid.bind(this.display), 1000);
  }
}

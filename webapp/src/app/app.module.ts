import {BrowserModule} from '@angular/platform-browser';
import {NgModule} from '@angular/core';
import {FormsModule} from '@angular/forms';

import {AppRoutingModule} from './app-routing.module';
import {AppComponent} from './app.component';
import {ControlsComponent} from './controls/controls.component';
import {DisplayComponent} from './display/display.component';
import {OptionsComponent} from './options/options.component';
import {HttpClientModule} from '@angular/common/http';

import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {
  MatButtonModule,
  MatIconModule,
  MatCheckboxModule,
  MatDatepickerModule,
  MatNativeDateModule,
  MatFormFieldModule,
  MatInputModule,
  MatProgressBarModule,
  MatCardModule
} from '@angular/material';
import { MessageComponent } from './message/message.component';

@NgModule({
  declarations: [
    AppComponent,
    ControlsComponent,
    DisplayComponent,
    OptionsComponent,
    MessageComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    BrowserAnimationsModule,
    MatButtonModule,
    MatIconModule,
    MatCheckboxModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressBarModule,
    MatCardModule,
    HttpClientModule
  ],
  providers: [],
  bootstrap: [AppComponent],
  entryComponents: [OptionsComponent, MessageComponent]
})
export class AppModule
{
}

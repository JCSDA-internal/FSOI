import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from '@angular/material';

@Component({
  selector: 'app-details',
  templateUrl: './details.component.html',
  styleUrls: ['./details.component.css']
})
export class DetailsComponent implements OnInit
{
  /**
   * Hash value of the request
   */
  requestHash: string;


  /**
   * Object containing all of the request details
   */
  requestObject: any;


  /**
   * A list of strings containing any error messages -- may be undefined if there are no errors
   */
  errors: any;


  /**
   * A list of strings containing any warning messages -- may be undefined if there are no warnings
   */
  warnings: any;


  /**
   * Construct the details dialog
   *
   * @param dialogRef Reference to the material dialog
   * @param data The data to display
   * @param data.requestHash Hash value of the request
   * @param data.reqData Request data details
   * @param data.errors List of error strings -- may be undefined
   */
  constructor(public dialogRef: MatDialogRef<DetailsComponent>, @Inject(MAT_DIALOG_DATA) public data: object)
  {
    this.requestHash = data['requestHash'];
    this.requestObject = JSON.parse(data['requestObject']);
    this.errors = (data['errors'] === undefined) ? [] : data['errors'];
    this.warnings = (data['warnings'] === undefined) ? [] : data['warnings'];
  }


  /**
   * No-op
   */
  ngOnInit()
  {
  }


  /**
   * Close the dialog
   */
  closeDialog(): void
  {
    this.dialogRef.close();
  }
}

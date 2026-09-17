/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type FolderUpdate = {
    note: string;
    status: FolderUpdate.status;
};
export namespace FolderUpdate {
    export enum status {
        AWAITING_IMPORT = 'awaiting_import',
        ACCESS_NEEDED = 'access_needed',
        IMPORTED = 'imported',
    }
}

